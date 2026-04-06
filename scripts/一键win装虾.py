#!/usr/bin/env python3
"""
Windows 一键部署 OpenClaw 节点（Docker Compose）。

单文件即可：内嵌 docker-compose.yml、Dockerfile.openclaw、Dockerfile.orchestrator、
orchestrator.py、orchestrator.requirements.txt、openclaw.json（仓库主架构，密钥已脱敏为 ${...}，
zlib+Base85），新机器只需本脚本 + Docker Desktop。

用法:
  python 一键win装虾.py
  set OPENCLAW_NODE_DIR=D:/OpenClaw_Node
  python 一键win装虾.py

可选仍从源码目录覆盖同步:
  set OPENCLAW_SOURCE=D:/path/to/my_openclaw
  python 一键win装虾.py

无本机 Clash/代理时:
  python 一键win装虾.py --no-proxy
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zlib
from pathlib import Path

try:
    import ctypes
except ImportError:
    ctypes = None  # type: ignore[misc, assignment]

def resolve_gateway_ports(node_dir: Path) -> tuple[int, int]:
    """(宿主机映射端口, 容器内 gateway.port)。从节点目录的 openclaw.json 与 docker-compose.yml 解析。"""
    oc = node_dir / "openclaw.json"
    compose = node_dir / "docker-compose.yml"
    container = 18889
    if oc.is_file():
        try:
            with oc.open(encoding="utf-8") as f:
                data = json.load(f)
            container = int(data.get("gateway", {}).get("port") or 18889)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
    host = container
    if compose.is_file():
        try:
            text = compose.read_text(encoding="utf-8")
            m = re.search(r"127\.0\.0\.1:(\d+):(\d+)", text)
            if m and int(m.group(2)) == container:
                host = int(m.group(1))
        except OSError:
            pass
    return host, container

REQUIRED_NODE_ARTIFACTS = (
    "docker-compose.yml",
    "Dockerfile.openclaw",
    "Dockerfile.orchestrator",
    "orchestrator.py",
    "orchestrator.requirements.txt",
    "openclaw.json",
)

DIRS_TO_CREATE = (
    "workspace",
    "agents/main",
    "agents/director",
    "agents/architect",
    "agents/researcher",
    "agents/validator",
    "agents/tester",
    "agents/executor",
    "agents/creative",
    "agents/auditor",
    "agents/auditor-code",
    "agents/ai_customer_service",
    "agents/censor",
    "agents/writer",
    "agents/writer/knowledge-base",
    "agents/scout",
    "agents/worker-code",
    "agents/worker-doc",
    "agents/worker-research",
    "agents/auditor/本地ide集群知识库",
    "identity",
    "openclaw_state",
    "tokens",
    "container-data/copilot-cache",
    "container-data/playwright-cache",
)


EMBEDDED_BUNDLE_Z85: dict[str, str] = {
    'docker-compose.yml': (
        "c-pO3>rdNO6#vd&aYg%KlbSftb_GkBlqN2X2slcN`uJj*_%?BId_DVy$0{baiPr|BkBvTH-PA%`sVmUe3WUc$6FbQ#{)JsXaUN@j"
        "I*=USbARWYd+vE!huWx=gF4*-Kn|&rjBrRrNVe7hNJSwJX&?wf5g~>00C^Rk3+WCgEejax*oNnjf(1!|8m|aN!sp_7OP~$V2vX26"
        "4N8g(bv>kGq^eM~_n<P$-;iX&7ACJY=@h7JFB&t8#^#Q(wroCnS6_VtdLlhNM|%sE@^s~31t2X~AVM_(BMlfc)7AYuwT;92{S8Ov"
        "xQcY>*aAQZbQ0!Br@b6Sa;fOp?d*jq|M($Mz=CgWP9Q31N>Eiw9Cqz276nD5!Pg$QiZpDUEaDOLl1i=tqY<cp)3@SmI+<cQK0B0V"
        "GCarjGlP>J5-P&54EX?qw__^?SS!H>3a<*d0K{R+UWN5<WC_Ew9)#Qk<YlQSVGwcefZPsWKspW>+i9)CBFc?GEi5S*YKkD!7BQ43"
        "0>*@i&JF?&-mb$uT#{tblVe>N5l=kk5*&e!7Zd(_I4I_$fzkpzVZe}INkd8zD%d;YDK{#rEAMKDj~hY~7#lmr!xu+;b0o}a@3)MN"
        "!^(EqT-`m|oA+;ui)H#4jvvaTq6LgqnxcXt=%CMm?N~mM%tR^Mk-EQ=X4w>fDVbut9p}fE5ys=#2eO&?WhTpIVjP>{(`<%|_C$Ik"
        "?IM;KHvPJ?`w}<;L3L%r*#GTl?@=CNCyv7E1Tp@hF}+Umr6Ezq1e_~~C=Y6zWn*bMkOPh|I(U97wu7P5)qNoxA^%;pbu|0oq?8C%"
        "sE9g`lw)+TrhI-l68Sk<82g-1bVUTqn~ZXTO!>l9S(q5pq<o=$QS)#-DG2{lj1sq}nZbA}c7>0#gO`$hd^*Nmj@l*1Qy0FeBc&C8"
        "h0XM5)3G??pvRClqN_p<wjyJF%pjNLGc3zFSYo?^bw8R0N;(EbD=^$hBhld7N-V@~4fL-Nd?CUcLP^HJ-UX5lz6<O|0aZXnNGV8!"
        "$K)?t50>R(9OGn7gM1%(nd8!YI>TPQ=A~fUaJkUad!d0Rdr~F~$g3I}pEwzhep04E);*dXdKUhSpH*ktvHP3~a&?`UGaJvutnL#_"
        "C;5KnTJ-d-Cdy=6C^MKyv&liO3Gb0xnYiQt!wv=UE~OPZ5WC7}7%r1!vH^I2+RAb%mP%cW#rydIHo*j#8t9Yl>!rEyLv4S*KD}7o"
        "-!PYFE9Jk9y9=Np4MKsSw=<4zO+s253!wdsquVB+r`25ji!>HjnP00HD*J~{6Ec=IE9G@_{=k^qGUunv)p-XCS~EKAW-i?>i%H=k"
        "es_7Rf2`LwXN=u@=EC=tooQoXxkU)&Fi;~38k3=zhoNCXhe6Tp5l!X+p(ILHXCZbPt6RR}R(&pza)6Qu>nk(WgEgO{LG`D=fm65!"
        ");11|wb|P4%Sw6QZtPRWPjAhw?fTSq?fFw<=577y<I2u65(H$ZBx7Rz$%A0G4^u>mf+alRoWooBiipFizrOG%1;>%*%3-Da)D1Y|"
        "RYw!BDjy(dbMAwA|4-71&EJ2lKfG;h?$u`BIVUjIUf15Ow+X(s6}Qz~5HDz`D3yx9e7{tCK1U*{x_8fbMU0xOKX_xldg6pveRk2f"
        "y=mP3g}j){Tb1pfiPIVlZ<>COyP!7!YY1T~Y%i#y9%^cn*0JhS<=VlW+THE?vnBV4iywRyqNHO<mU-uz+=1GmePYh&>LJyWJbQY2"
        "J3nuTaK{uGO?Z5yd!v$;JFXJ|*wb@h4L}hVkv2htbA8qr@+}le4iGhp*zlPo>p7wrQL?0z#;wmIk~Nm=biELAmLL0AB2sx*>VFw4"
        "T4#v#P%;tiibRg*(R5!kg}WY&>5@QY3xbj_2$H`slqE%UFg9S-)ay)w6yO1tbY+W7heS9!*@#TXvRN{EBpT5k)#m8xK6~!`SI2zb"
        "CLfE(nQS&1{H`HqznDtKtuEwF$s=$=C)vkCvHSe_uHLX(8b0m?LkYI6loZ=Xrip~reSCVG?>w3!E%YYL;r3<xqZPNYSx`g7uR2u}"
        "a#Wajx#_@kJ1b}neInYs$)ElB_o>=12ps|Qn)0io;~xiMh}i"
    ),
    'Dockerfile.openclaw': (
        "c-mD_J!``-5Z(PN4hk6xvg5Q<p+ia>=uoG)%~mL9>tc(@l96P``S-m*8arBa@8k5O)3(@sK;2X>RyMI6nM&j7R=j8o<U<tgzp?_H"
        "wOkha9Iy+brT~2>*#L_LY_hlab^g08cKLUfZ(fZx$^>#)1vSvEK^Y%VYY=A;!dP*|!ck@0mW=f969F%+O5;2CJcs^iLKu!|ycElc"
        "k!9~iD(*bKQ>%N|$T^+$Do{EjCAL`KF$Xo$Ja2Spq+3lyUAA-ovAjIMnpqTj+Z*}c!ZUI$2zP*FK$ozd@KAX7!6%PV^Z=h4&nKtq"
        "hR5Wg;XF+e$}@z9fKMY(ms<i0P+`@uI4Fd{>b|A;`bWk}iv9q22$9Y"
    ),
    'Dockerfile.orchestrator': (
        "c-n1|!Ac`R5Qgvl6vZrf5Id6)1P$aMaU`N~B<iZT9@?4GY3!M9t1Du_lV`;}?4EoF!IP)>G^_4o*fFA@_NA$6{`$Yada0lGzzw;u"
        "RjXNRG^97W6k<E=uPiS2Ay&=_(cfAF<yame!@%W=5vHczJG%0$i~%_WDJv`AYDt*cvcxL)kPXPdF9G2MA(bHM5aLrsvC#*?gTw9F"
        "$J0V|()C@ilojZi6kDnho(wc$n8d!uXAGYkuY69s50WuPros%FYYJvxCExhCA=HHU0c?-4^6-3f`#Adh{O1mGn;j#`kj7b$@OX9q"
        "bb0ZAG<v%J{qNyM{7hH3dI{`B@kANz3z6)sryB{()#vL%bd!bE&2FcgbXEeIt{CZ5nRc`8L&>^CJK*;0xCr>f(jjS^w;QkTgiIQJ"
        "yZN@iPH%CtPU#P!V0NuIHa1hHu%26E!?-|YxPbF>z%$Lz2w{V0FPeOFGy~D6+=2K7zl*ZY"
    ),
    'orchestrator.requirements.txt': (
        "c-l)#EG|hb$h5UJ&@(hN)idKNEz3;KFUpGs3g@LH7Nx|3q>N4U47f5%N(w4KJR=J|L$30~lH`n({B&DeGd%;KEC69g7A6"
    ),
    'orchestrator.py': (
        "c-rk+>2ur075~n^VhfLFz?y<6`KZGw)2cFUsdYpRMNgVhH5iy&iWrdq3xGPJs3XU*EGLp>JHD;h@)diWNIv5Fl8^tTBY@<m{0n`1"
        ";36p>jnWUD$}=Xg`}XbbJAUu&TWtGHXVo-1535=y*2Ym~$|~yG&WIogy?RA0=@!cBV^~9JBUi+xWhj<zpz&@g9*GR8d7M)WRDW>P"
        "e(}A1>F&=jFGo7igkt52d3_Ysj;_|OoOVv$K~kqhn3$cYc4f_eb?)bv3-#mo?62?Euivh%UvkbrKnMB`$%s+`i;P~?@*No+R)uz;"
        "#^ohv`9)*)guQegM%vGx*h{DFwG;L+m~q}J8d%Az+Ng9;&yD^3@&t@$%<Z-7^|kA;DCe8+o%wrcSG=opS9~Y3zg@InoCQwK{U2&~"
        "&eUGqu}_?BT)O3~uG>pbVR&QqjQ#3N<M?9z{y8#y@dmWpr%u}UpQCgIYrQ390@-T|uz<$wl5_DSjM>%w5who=+KZ22ME%b9u*Alt"
        "Q;pecWZZ)}wl(COeQh7Rjk<Otdw#BQ=Gw-~)3xOl=iv%)a4tV?EI&e>rlnX_6FDbu+e<e$USFxdIaOPK>|DEDTmA+pYhOQcW{*T7"
        "wIA+7e**1|e-w{^Se=#Q2~@PKN}{tf$5ba*biI_=8{Zp8VjhHp4Orr_+N;x1<jkLUiMzUgC&l4k7opsXM0@Sc#<O*hc$8Q{B%+op"
        "x?v&Rbe}A>jNNBL(eirP>v47AHk9<yQSw?a^fJmT7A9j6?{wc;Z%!|jaL!V7&GZQH->W#nx?QW1^us1L#<Ag1rFlaW9UjM;<q_>y"
        "OL%C?v~W2^+WTPHC3i?c0g+c!j}%^e2K!?uL#8(^@?chASvW*48NAh-<Ih9s0gsfo5gAXqFV%51ryE)%vJG`?-5+pk99yitTC*2k"
        "Y%%9-`Y)*gd0&49A(R9QkN_f7L)WBHY>9%`E5x8*;65%yBZKMmL3w}w!BpE}UT<g^`=J&qS(6rU$@XLpq_Xm%%)z#kd%c8>u$kcl"
        "pP@s8sf<h)+lEhXda(asIx7dLfT6${br41!Ce9hy>gbMl?*V=X`-ify@4<8?3;a~g5}SFZGrfJOp=_ono6b-=!jbr?5RDS$Gk9R2"
        "Q@i{X^XS^jk;q`?&_GJ=P47z$QPE8UWW@ltcFy>tD8__F^@2e6r9U0u1Ie)NkH`o{>s)x!xB#d$4_HUw(IX#9^$w9)0F8c&_QVm|"
        "<^vOqc9v)DTX%w3==^xyIrjiKH7-7KR&O{LRsiDc*Y|2C?-RzK^!!!Mq_UZQx`^FdZ{~ov_QP2YfLqI)1C?}GG1XkJt`*c#F#<Y3"
        "CBTtV((Uda*q@Hk_JVGd6)P!h7Zo!{P%LVq;q4+N*A((Pg0_ogY?{g_ya;R*fxJSQ4EwBOd%0tK9&PVSZ2u&&eFzAmWECJecQUZ0"
        "gYbwAQP2a?7fdkXJ4*tY*cyhe5f}-NVid7IP~hYB`qQH%xa5E^uTN+)09q9%7_b68{beJzA(1kTft}r~eSd^mjWhpKG(x74OAtR`"
        "L^#@t&}mdPoQLkw1S+YfHJn#-7Fo;i2=Z3KBC&Jfw*BTpgv2+KSgBy?mQs=p2D7G+KymOB#*n{|g?lgHgNBMJ-ArWbt&8P3wYBTD"
        "Q*&F)JdX>YRV6PotP`UNY7G!xiHn}P56KE-4IAqxkq@2r*DLi`uk4d^_R=GkJ&<TjhE1qe5qU~stjM2QAm~<6tfGV`K^3Oxaf|v?"
        "9tRyV8J~j4SBN6TM1?RdH+E3229aB9*G>K`Vz@vefhnpLFpPFYutEz66vHyf5=3FNSe1ondybT=9~6{)UbGlnFg8im3c6SjhWiKl"
        "vm<B_D5!*SK7po7urYsRbcV5kossZ8?QMC6coNkO@MfxE!@#F3BcP*Gr@@Ifo~=4h*Fh^JTcu<y7j+hnY&<_^FPwi5^{^yRgQOY+"
        "8SvrA+xAReqwk?Ug{iO7MnRQ=G-0R~X3QX^7XGFQVV*&m?ifKspAGb;_JJ(vh~Y%n?vWWulF%1yXQui&PPWL|lPC4z7Kz3XV27!*"
        "7cdt=sai$3ps1y)frWs)X<)Q(J#@~^dy=lNJ%EEl5J=u7?|>ZhstE^`7Fkjx8g>z91nq!W=ym$QCMgw=bzYnf2~6Pp4O~zs0h4?|"
        "#lm!K(?G!<ntBxrdfZG{s#-ZspAe&xYU(V)h*5vQjBoxEilG4t6K(wl%%9{9ZM4N^Oir`k8PJ}A%Zf@yzD0Xpw0Mh4cqf|Lopt;8"
        "3oq1=Qx!equ-v0@@tQrq1)2&6FjpaN#G;}j|3N6*fkOFBv_;!Iqy)6xB+q}0cr02aN|10mG(%_Sp7=}|{Q3Qa3#SH%;aFzNXcG|N"
        "xVZG7_To+L?l%w<?6u3z@-+}QlczoZ0A3;c<I=CcxoBUx>Pg=dbP<j_C~H8h_qGpqMdG(Fsz?Y<+Nj0n6c#^%!&6h!aC~IAYXtp1"
        "Nv3JVAFd}E7SN>0ie4$<g4HHoyc-6aVG9(OfwViFN$o@YNXh2<a2WFzLBwU2Fs_I@;~u)HxiRh=QPlA<MYAu^fUaRrixA2^r9j{a"
        "Rxmc6&2Buq_udhm1dGig1tdgOL!&cCn%da8T*?)7HHSr#m<6{O{T0%uPx-+cjFwk@{L>?=`qYlDvU<-J&z&nNrpeMbx(G;^+aLG2"
        "mk}N6nha+;fZe=k;!+`oXt^L75<P7KB$o54fpg%sQ|-jx&Q{{m?kLH7YpW;h*T?L+O9T+t7M%H0K6NuUKd7^LO(Q3hT<)!jnT98r"
        "C4y%aB$Ap#>}Z#P5leDu-zx+2QzCC%m?JKkIMLQ0^Z0O;BIzGSQ2(d~XqN{w);bRK9YO_A47g)>i$RaWlQ~?mP>TMjx<)qMG!K~r"
        "8-{N1=(is-2$;gsNxaK*WF!-{%tK~oP`uUF&x=OLesQ*T_U;z5hj0h_<x_~3YL#%(E6)ZCvqB7!${2_(DRfJ5y3;?xXjYcsl|^V("
        "%qcBL{eU$E;t#7fvNJX-LB0#5JR~J2fH0JX;y1)aP7#g)jEdt{u!a^$xCCz!$d<fkKQj{e1klT$0(~^_3kjA01ls)!k1+LKhC90B"
        "iIEsRK`+nN-<(F>apZh=J;GD4kVuPIDOtskNLiCBQogTgfeSx@1bvLugMvG1jzI1lN=20oy$XrD&^b*kIKkW{hRWC~>UlFcEF4JD"
        "^3q^>i2WX-Kl@S#Q`r=4=*jl>k%#nPwm&^EB#Z<XTQT&>DUlz+6Mo5)PR5dUnVh?)5~R`v`ilorm8C^E8f~oKgab36J_~Q${r)v~"
        "201_7CB^POa7t{@mint7?WNQ8<3FKbp^kR3%$}9zU5f+IVw0nflPFMK@@=mf3O-RL5ib)UaXK($CQ85oJS9(4I3~>??r=SMwwKd2"
        "3$P<8qzL;2Qc5NF7>Or~N)=*D9w`M2cIMV4V%(b`x69+??)Xly6<+^1Ht*b=b*|lJ8FJ&u8~fNII;`iXQ2qWoNX=RJvi{Gf5ijon"
        "K?k#pNa*~int^1a-P%KF*}M_PgUTHk;c~^A62fPard@<P%Q&wpvNcr!2(s{`)mbS)&KuysH@z8J@GQKk^ux1pS6oZ??B%<S@2(;+"
        "?#{kc&%RD>ydbWp&ciRA3r|39RDixXf!6KzrKysPn@%DzmyxP)b}%4ugN$8torg>jbdf+jq)JMn!`vjpQIB^j6N+ki^N>c-Q@wNb"
        "tH$gKGkgLK;0mT&K!ig_UgmA2AT~og%rUhRY!!;SX|b9#)no^t#VBA7v;gXBW&s-=SOaYl{F`xkqcMmDWRvc)I7dl^q{st&E}}81"
        "q)$+(@Y+Oh4dLM1wCv$AQtKOUx1(X92hR7pp?<EAKrRr%g77D-7~nJ0fqMIl(0;g!5iC_E!<p?8sZwaE!O3XtYVhiid5~fNIMdmt"
        "{cD05*XJosMKP2z5icoMy7(u-|HhQe`nU!|c^bn_YTEQ-N9rLBy(JaYB9i<MusXRXF2!lSmZR;>Iip$eEQS$Ce0H%VnPL{33>$E)"
        "g{*3nl5EedeO#EyCgHXcx-dbkx3!mvB*}il-3**~+Qy`kWs>l6xXtmJQ@Xk*DFUQ%(`+{%0?*Y7#44<m5!XTs81D+LbF=iad3}dm"
        "wwO)B(#Ll#s^G4QkT)-++k*y3?LuLXH29!pR;0i{;*^2gp+vY$6|B^_RW?`!(S|(T%qqA8j>c{TYbt>?AFfF#CMpsY%OZgTO|$U4"
        "qYJ_-^$IvEFi(U-c3>KC*u@*%d);gG1qz<_(?_+J-`cAe$z{^=EbUy6v^(Ck#KY!eO>12Iz_`v*z!-~-JTSI~bbn8^D~};VhIHSn"
        "2qSxL5pW)k_|A{lSuBE$ZaiCLw`lbTM}eB<T#?NHwGHffTipEg_{)*$gVE^&5b9kh^+8DWZnSy_V)>}`o(Ilf<ma0>bNJFW(OT&Y"
        "xb%PMuk1pL6&hnSOQqf$cGR}c9QNM-t{1ABCxiEO#s9m||F#Q3_*lJZKYQkVxYd|l+IYEATff8*)j9t>;>w<I-z29d-J!(VO{l%>"
        "xot|_nt8WNvcbbYJi`vIs5MUvZpF>BBX2$Lxl*Oe;V-dByK`MLB>7aX5jC%XQT!UUGj;(^N~B9Se}#*8awp?zLpP<eG6qLj!xX*p"
        "bPUn!a#<fsk}DI>=(;52UC+1P#`CMAz@@%Bu3O?;YV#>1TLu4O4K(V0yvEVg?U77Us;HK*7%FQ=V<@m{1LvxSsgC31eg%%D%^XOP"
        "SKREvoN{F8HUVwF!i}cA8EB=HZE2^wCH_g#ksJ1{#o$#{#Qg@q|3D;5pF{>&$+q`iF_c$u8FE!7cgo`(3-9Hz!M#Z16Cyea=aHy_"
        ")f?kVDY-LlM%^8>@(F#<O72H6xwu0BUUB+0WIQn)_|VJEnOphn51w3z^!x*-FTP!#MergnZRei@N|1JnN~ID*<e;Av`1}Hieuk9{"
        "tRhC{m)RFd0>81OHC|FElgU>{vW${RB*-!`dRZ2j)iV!>{2NEYaxn"
    ),
    'openclaw.json': (
        "c-qw)*>c-B^4(wIQq9Bcl&RBK{IrU##2O#+T5__PEf)(SVG1LXU;t9GlhVI$10+T85+(VVxbhH-=tg&=8-0>LcXoGc4)#&)WcMfh"
        "4Zm!}{Sgg}2{ylA#tC&{t=4X~59^(J`?$831MB)Rgx1{Gnw?RzbJ96FIXJ8z9Pj^C1NenNs?Es{#LP6M+rV9cesKJkN)LdmSOSn!"
        ">Nv<1bZRCwe9AKGSJcE}(WVBn6Yd<$IkGTM_#^I^25!PIJTkF(WZ)|S);ef5_u`fD)9D1cF18hLc>I6~p9Ju%-E20a#|!!YBI4?M"
        "fCH@3a3cN;YTMZGYkS4Sn+kCQd6Gl|%BXl!;{lunBR_C$C#D=qivoX=Na`{AKx{>Jc;<4$(7w;Ht3ANErKJM+88I;vB&dg7M3!7C"
        "0w9m*Q~Xqm#okM8?GTqZ=uvCE{MM4|*V?!JO8a(RbYBx=k7GR5=)(gs2(n*vcZX7!Pw2~91(-W>(2H(q+0M(#9og*U$!8>ZiLEo&"
        "Qh?ct3yRSk%q$%Hv6#}@*L93IzGK1!Y7^i0_(`JyeAKz&V!v*<;zz@_oyM%CvJ6izfKx#F?dSFI^i=QO^!1D0H@&sUfF&Yp26a3e"
        "`{1H^R(vVf|CY~o6%IppD_!<~K!lFgX@1nYosU}I<vt4xUuz#UkCY8Vk&%PbD4&Gr8K`ymlYk5(PF><!0RDh%jx*~9b$$Hke<iL-"
        "=K#}bD=s*e6FrXT6uY5^Ztp9ri{;<<8#%=Hq`WH-;R-~!YS$0Sw57uQE?CoA|9Uf>wGR$gD{a5|;ZRlD-g@@hbH>;-fe-EY<7zWi"
        "A>Um5<JO1v3gN}_CKg*1XWyT%X?G65*|gggid%xcsMf%{RVl62K3;9JTdA%6s%mThs%mS$bG3C|Rc)PLRc)PjskVwFyhM31Rvm;|"
        "p}4bN?`GKRUBt?JP1P+02@eyqGUc5C;7|a5fx`T)RCc)kVj3$hY)TXr1B;7RuBWTP;CgsI7`=s_ro<uIbVc%YApkB40RFj*>!7u+"
        "a*7JXjA}qLt@cs93IAFrt=4{Le}!fSmzUkE?px@^r4BK)S-VUv11VXU8){$LzfK8rm~^eyONT{}>YN;pD<ln_d_GtH$0Xf2?;l%O"
        "b2=wB@^QZA%t-t3b5FbKyu&O%*FP!ngo6M2m{{^Q#5sqD5O2)(%WmH1%d5Azc0fkkuODfjY{VyJI$8<zYC76D&8Rd;yeup`t3>UU"
        "gS`WTT-AUpuuVvP>mg`GjP76eue$%$&%cds`*&|)no1YsNShFA!aa=5HF_pT+BrZE1@!OdQnX*Fd$NgZq13W*r3Nhw*(UPI4BN=H"
        "0%YNOhzUaSC_^5L`Bj;x84NyO_6jwcDC@qY8w=E2U+Ko0_yGmB&$H8-Tyq_4lt~8C_S&e_dJWWIkC8FW8j*0tjdE9&Y5z9X?V>Id"
        "-bRu-u234tV&Tt`N~oNqmCGLL2{b4ULF;H9qng|R{=zeY=S6dcRQp>#n_x71(tQSpl3Eb@u?gbJ{n$Mhu)8A(n-bGQ3^_c556|IT"
        "Fmj5^4B{FLJ759G)@k5-fnN;g69-ed*b+%bX}%N@OUjy^>^(^iVouqVd&t01rh3!6KE3RI)xQpIFNQbW(_Ui9H3vJCJq<Bp#w2}o"
        "aR0|PHgjyRF{_Z5Fx{4J6tp^Xj0<mr3_l#v{>;xmqAR45W0+$$!%HX9EM;Xq`_A#?Pl!7OhR-6}a`rn<4seFqm~yNvL%pt?FM2$s"
        "t`RT>wjjLV{&I;2<BX3e#AvmPM9Saj9OoRl=9oSfAEjWjaH4DzIRJ{?hk_c$9tROOM=J+q5{8xO`AW0we(qh5hWhPbFj_R0h?OLS"
        "#S&kgaj#1w!K@@A%u9gd%_UJ#E6L2j8JTFC^GYx)iHKTb3ppaR%I)zZHiB(LSRz)E0GBGG`Nkxch}BjVm}DCv3h?s5Jrm+q2j#M0"
        "zPpV-QzLRg$S6Ao$p1{d?OEiI-}QkI-3Yi(9n5qQafq?SxfJYCZSxS<wy?)M+Iv3zIV0P+t_ZDidv1snY}4ICtZLq2FTCYVQgPQM"
        "WKv^WIs$cFGI4m@mevwKm4)0d%O{^w^<5UQK3PS^rWd~(m*i>4o@z6y-pd*?yhr5?IMdQpn)gx0!!hTwz*P#f8R2A1Y~stS0mN&m"
        "BuVCNBigmX6m5x?&Y3d>;TS4mNF<XBv_zBJ^@|fHNVxoLYHloF7R(-l6dLSuxgFB~CRq1rpwE@OO%<kyi)=J|9us_mU0_3h3efs2"
        "WE|KFZ~)+&v5@gP&tqXs(B_Abc1+J>;Kx>Hkk7K8$AyE5ZUy>}fa+7~S_M|Q6WvTv4T@KB6(`_^Nt`rLpT=*rg-?f5VoQgSS_3cR"
        "BbKhcYjo~nc1E~oBYC|UnkR4aPAHu!B#Wxxnup~3ueC-996j|#4H`9$x})CL?l=8>Fu2f1gNxpETyn=X>@ajXQL9Ppa}u7MW+5NX"
        "fw4Ws@!jI@0Z5WUQuvWD*i4ph7=9p+SdG;ojkM>B@VcS8Q_!-^OI&BpD;3y9L9J9!*ksF)eBF>w^Yi{_RXSD+xXve(`MT1XC=A0z"
        "A+t2TWiMmaL1n!~Dhtj8x9GkocD8)gyCjw<F-_j4Ow%Ca=d-OY&kJwgZ$Cfv`or@({jB?Ezc(6)ZuO1cKU<`8J%Ar#(1Kr%Gwhw-"
        "_C|{&p<Ae_X2B(|Wa)0G56=g;qfJ;!;jCmS6@w~y>E507M}yl<SW!``Ia&JQN>)yL*Tc;?Q7~3Al8Q)`e0;s_k9r&Np<t}!<Hu$P"
        "GCUpJZDb?~LY|F+w{E0+?uNIlAcazzm2icPxRWjO1w7`|m}2#-3o0FHJ}wGi;gN6RP!g^;@Jx0DlMS33Y7^rrZni4^ML6$Ij5?`;"
        "toBDN-F-4GVKnf{wgF!&g}A0Zc_0Szqf}T#NyTYDd62sHA%QidH_tdFaF*1D7>r#LvuotY$diJQJY<~KA6aEH2y+l=uHXp59&mA^"
        "JCj$(0W<j^h02KEIzB%Bu$O)nKKyJadMFa|@FDfaN!MRat{AoNi0Y1`SUF(CB5t|}j$a;;n@=eBPb6tI2g<)*A|Z0Bl2o8%hLFf`"
        "H~h>db&e)-EevPL?I*}!M1(lQBKj$?=}JZYR7W|8Fj-0To6lXkccb%k?h^AiLd51ED$bb!XyTGM#LsoKyS|Sd&kx^hS1U$29hBcB"
        "iRqxa1gANLfGgKJ&1TsbP*Hw_?7sIYYEh&IlJe}+fz|XV$%RnxK>n#R?#$R`L1~wDWN-^Sz{G3gmKZdTQ`uz>>NAr5zRH?tg!3Rn"
        "DmA<uUi2?7hx*Os-RJ&wGQ%vGr9vKTyu?l}&5v#p(K9pRttdoO>G=ebcgWGgS@mmE3&)NYepSghvYxMi$AH-@naqz0kztdyP%<{^"
        "*+Jw7pWUEIH)CuXUd;G@7Z`soS6(%(1ZVz0<k{wfy~5J-H<Pk#x=m`DZb0_JX6a9}qP4$?i^Ti0;n+33n3T$L)~U3-5@TXkzHcj6"
        "w5J?2JpH$%he!i>(&T`Z)iO}`so#stSQ~J>?CpFlUL#toc+C;P?yP_}SQz$hZ^Q+QE?IQ{(hnEe{TDlBzZR>U{mx?N|4TtmG5"
    ),
}


def materialize_embedded(node_dir: Path, force: bool) -> int:
    """从内嵌压缩包写入构件；force 时覆盖已存在文件。"""
    n = 0
    for name, payload in EMBEDDED_BUNDLE_Z85.items():
        dest = node_dir / name
        if dest.is_file() and not force:
            continue
        raw = zlib.decompress(base64.b85decode(payload.encode("ascii")))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        n += 1
    return n


def strip_openclaw_proxy_lines(compose: Path) -> None:
    """移除 openclaw 服务中指向 host.docker.internal:7897 的代理环境变量行。"""
    if not compose.is_file():
        return
    prefixes = (
        "      - HTTP_PROXY=",
        "      - HTTPS_PROXY=",
        "      - http_proxy=",
        "      - https_proxy=",
        "      - NO_PROXY=",
        "      - no_proxy=",
    )
    lines = compose.read_text(encoding="utf-8").splitlines()
    filtered = [ln for ln in lines if not any(ln.startswith(p) for p in prefixes)]
    compose.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def is_windows() -> bool:
    return sys.platform == "win32"


def is_admin() -> bool:
    if not is_windows() or ctypes is None:
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
    except Exception:
        return False


def wait_for_docker(timeout_s: int = 120, interval_s: int = 3) -> None:
    deadline = time.monotonic() + timeout_s
    last_err: str | None = None
    while time.monotonic() < deadline:
        try:
            r = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if r.returncode == 0:
                return
            last_err = (r.stderr or r.stdout or "").strip() or f"exit {r.returncode}"
        except FileNotFoundError as e:
            raise SystemExit("未找到 docker 命令，请安装 Docker Desktop 并确保 PATH 可用。") from e
        except subprocess.TimeoutExpired:
            last_err = "docker info 超时"
        time.sleep(interval_s)
    raise SystemExit(
        f"Docker 引擎在 {timeout_s}s 内未就绪。"
        + (f" 末次输出: {last_err}" if last_err else "")
        + " 请先启动 Docker Desktop。"
    )


def resolve_compose_cmd() -> list[str]:
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return ["docker", "compose"]
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    try:
        subprocess.run(
            ["docker-compose", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return ["docker-compose"]
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise SystemExit("未检测到 docker compose / docker-compose。")


def sync_from_source(src: Path, dst: Path, force: bool) -> None:
    for name in REQUIRED_NODE_ARTIFACTS:
        s, d = src / name, dst / name
        if not s.is_file():
            continue
        if d.is_file() and not force and d.stat().st_mtime >= s.stat().st_mtime:
            continue
        shutil.copy2(s, d)


def write_env_if_missing(path: Path, force: bool) -> None:
    if path.is_file() and not force:
        return
    body = """\
# --- Docker / 通用 ---
GLM_API_KEY=
COPILOT_SUPER_TOKEN=
ZED_REMOTE_USER=dev
ZED_REMOTE_PASSWORD=
SCRAPER_API_KEY=
SCRAPER_API_ENDPOINT=http://api.scraperapi.com?api_key={key}&url={url}&render=true
SCRAPER_TIMEOUT=90
SCRAPER_MAX_RETRIES=3
SCRAPER_FALLBACK_MODE=browser
# --- 与内嵌 openclaw.json 中 ${...} 对应（按需填写）---
NSCC_API_KEY_1=
NSCC_API_KEY_2=
NSCC_API_KEY_3=
DEEPSEEK_API_KEY=
MOONSHOT_API_KEY=
OLLAMA_API_KEY=
MINIMAX_HYTRIU_API_KEY=
GOOGLE_API_KEY=
GATEWAY_AUTH_TOKEN=
GATEWAY_HOOK_TOKEN=
SKILLS_PLUGIN_API_KEY=
SERPAPI_API_KEY=
FEISHU_DAJIETOU_APP_ID=
FEISHU_DAJIETOU_APP_SECRET=
FEISHU_US_SHORT_APP_ID=
FEISHU_US_SHORT_APP_SECRET=
FEISHU_AUDITOR_APP_ID=
FEISHU_AUDITOR_APP_SECRET=
FEISHU_CENSOR_APP_ID=
FEISHU_CENSOR_APP_SECRET=
FEISHU_WRITER_APP_ID=
FEISHU_WRITER_APP_SECRET=
FEISHU_SCOUT_APP_ID=
FEISHU_SCOUT_APP_SECRET=
"""
    path.write_text(body, encoding="utf-8")


def patch_compose_for_windows(node_dir: Path) -> None:
    """将仓库里 macOS 绝对路径的 SSH 公钥挂载改为当前用户 .ssh（若存在）。"""
    compose = node_dir / "docker-compose.yml"
    if not compose.is_file():
        return
    text = compose.read_text(encoding="utf-8")
    pub = Path.home() / ".ssh" / "id_ed25519.pub"
    replacement = (
        f'{pub.as_posix()}:/keys/id_ed25519.pub:ro'
        if pub.is_file()
        else "./identity/placeholder_ssh.pub:/keys/id_ed25519.pub:ro"
    )
    text = text.replace("/Users/mac/.ssh/id_ed25519.pub:/keys/id_ed25519.pub:ro", replacement)
    text = re.sub(
        r"/Users/[^:\s]+/id_ed25519\.pub:/keys/id_ed25519\.pub:ro",
        replacement,
        text,
    )
    if replacement.startswith("./identity/"):
        stub = node_dir / "identity" / "placeholder_ssh.pub"
        if not stub.is_file():
            stub.write_text("# 请生成 SSH 公钥后替换为真实 id_ed25519.pub 内容\n", encoding="utf-8")
    compose.write_text(text, encoding="utf-8")


def compose_up(node_dir: Path, compose_cmd: list[str], pull: bool) -> int:
    if pull:
        subprocess.run(compose_cmd + ["pull"], cwd=node_dir, check=False)
    return subprocess.run(compose_cmd + ["up", "-d", "--build"], cwd=node_dir).returncode


def wait_gateway_http(host: str, port: int, timeout_s: int = 240) -> bool:
    try:
        import urllib.request
    except ImportError:
        return False
    urls = (
        f"http://{host}:{port}/health",
        f"http://{host}:{port}/",
    )
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        for url in urls:
            try:
                with urllib.request.urlopen(url, timeout=5) as r:
                    if r.status < 500:
                        return True
            except OSError:
                continue
        time.sleep(3)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Windows OpenClaw 节点 Docker 部署（单文件内嵌构件）")
    parser.add_argument(
        "--node-dir",
        default=os.environ.get("OPENCLAW_NODE_DIR", r"D:\OpenClaw_Node"),
        help="节点根目录（默认 D:\\OpenClaw_Node 或环境变量 OPENCLAW_NODE_DIR）",
    )
    parser.add_argument(
        "--source",
        default=os.environ.get("OPENCLAW_SOURCE", ""),
        help="可选：my_openclaw 源码目录，优先复制 Dockerfile / compose / orchestrator",
    )
    parser.add_argument("--force", action="store_true", help="覆盖 .env、较新的同步文件，并覆盖内嵌释放的构件")
    parser.add_argument("--no-embedded", action="store_true", help="不释放内嵌构件（需已有文件或 --source）")
    parser.add_argument("--no-proxy", action="store_true", help="从 compose 去掉 OpenClaw 容器代理环境变量")
    parser.add_argument("--no-start", action="store_true", help="只准备目录与配置，不执行 compose up")
    parser.add_argument("--pull", action="store_true", help="启动前先 docker compose pull")
    parser.add_argument(
        "--require-admin",
        action="store_true",
        help="强制请求 UAC 管理员（默认不请求；写 D: 通常不需要）",
    )
    args = parser.parse_args()

    if is_windows() and args.require_admin and not is_admin():
        if ctypes is None:
            raise SystemExit("无法请求管理员权限：ctypes 不可用。")
        print("正在请求管理员权限...")
        ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
            None,
            "runas",
            sys.executable,
            " ".join(sys.argv + ["--require-admin"]),
            None,
            1,
        )
        raise SystemExit(0)

    base = Path(args.node_dir)
    base.mkdir(parents=True, exist_ok=True)

    print("[1/5] 等待 Docker 引擎...")
    subprocess.run(
        ["docker", "--version"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    wait_for_docker()

    print("[2/5] 检测 Compose...")
    compose_cmd = resolve_compose_cmd()

    print(f"[3/5] 创建目录树: {base}")
    for rel in DIRS_TO_CREATE:
        (base / rel).mkdir(parents=True, exist_ok=True)

    src = Path(args.source) if args.source else None
    if src and src.is_dir():
        print(f"[4a/5] 从源码同步构件: {src}")
        sync_from_source(src, base, force=args.force)

    if args.no_embedded:
        print("[4b/5] 已 --no-embedded，跳过内嵌压缩包")
    else:
        missing = [n for n in REQUIRED_NODE_ARTIFACTS if not (base / n).is_file()]
        if missing or args.force:
            n = materialize_embedded(base, force=args.force)
            print(f"[4b/5] 内嵌压缩包写入 {n} 个文件（缺件补齐或 --force 覆盖）")
        else:
            print("[4b/5] 构件已齐全，跳过内嵌释放（使用 --force 可强制覆盖）")

    write_env_if_missing(base / ".env", force=args.force)
    patch_compose_for_windows(base)
    if args.no_proxy:
        strip_openclaw_proxy_lines(base / "docker-compose.yml")

    missing = [n for n in REQUIRED_NODE_ARTIFACTS if not (base / n).is_file()]
    if missing:
        raise SystemExit(
            "缺少下列文件，无法构建：\n  "
            + "\n  ".join(missing)
            + "\n请去掉 --no-embedded，或设置 --source 指向含上述文件的 my_openclaw 目录。"
        )

    if args.no_start:
        print("已按 --no-start 跳过启动。下一步: 编辑 .env 后执行 docker compose up -d --build")
        return

    print("[5/5] 构建并启动服务（首次可能较慢）...")
    code = compose_up(base, compose_cmd, pull=args.pull)
    if code != 0:
        raise SystemExit(f"compose 启动失败，退出码 {code}")

    gw_host, gw_container = resolve_gateway_ports(base)
    url_base = f"http://127.0.0.1:{gw_host}"
    print("\n================ 部署完成 ================")
    print(f"OpenClaw 网关: {url_base}/  （健康检查 {url_base}/health）")
    print(f"(容器内 gateway 监听 {gw_container}，宿主机端口 {gw_host}，见 compose / openclaw.json)")
    print("Orchestrator: http://127.0.0.1:8090")
    print("SSH (zed-backend): 127.0.0.1:2222")
    print("==========================================")
    if wait_gateway_http("127.0.0.1", gw_host, timeout_s=240):
        print("健康检查: 网关 HTTP 已响应。")
    else:
        print("提示: 网关暂未响应，请 docker compose logs -f openclaw 查看启动日志。")

    if is_windows():
        os.system("pause")


if __name__ == "__main__":
    main()
