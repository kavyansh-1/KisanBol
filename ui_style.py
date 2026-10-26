"""Visual system for KisanBol: a mandi rate board.
Ink-indigo board with amber digits, cool paper background, white slips, rubber-stamp verdicts.
Type: Martel (serif with Devanagari) for headlines and prices, Mukta (Devanagari + Latin) for the interface."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Martel:wght@400;700;800&family=Mukta:wght@400;600;800&family=Noto+Sans+Gurmukhi:wght@400;600;800&family=Noto+Serif+Gurmukhi:wght@600;800&display=swap');
:root{--ink:#14213D;--ink2:#1E3158;--amber:#FFB703;--paper:#EEF1F5;--card:#FFFFFF;--text:#1B2430;
--muted:#566173;--line:#D8DEE6;--red:#C62828;--red-t:#FBEAEA;--green:#2E7D4F;--green-t:#E6F3EB;--amber-t:#FFF3D1;--grey-t:#E9EDF2;}
html,body,[class*="css"],.stApp{font-family:'Mukta','Noto Sans Devanagari','Noto Sans Gurmukhi',system-ui,sans-serif;color:var(--text);}
.stApp{background:var(--paper);}
header[data-testid="stHeader"],#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important;}
.block-container{max-width:1080px;padding:1rem 1rem 3rem;}
h1,h2,h3{font-family:'Martel','Noto Serif Gurmukhi','Mukta',serif;letter-spacing:0;color:var(--ink);}
p,li{line-height:1.6;}

/* hero */
.hero{background:var(--ink);color:#fff;border-radius:18px;padding:28px 30px;display:grid;grid-template-columns:1.25fr 1fr;gap:28px;align-items:center;}
.hero h1{font-family:'Martel','Noto Serif Gurmukhi',serif;font-weight:800;font-size:clamp(2.6rem,6vw,4.2rem);line-height:1.05;color:#fff;margin:0;padding:0;}
.hero .en{font-family:'Mukta',sans-serif;font-weight:600;font-size:1.05rem;color:var(--amber);margin:.35rem 0 0;}
.hero .tag{font-size:1.08rem;color:#D9E0EE;margin:.9rem 0 0;max-width:34em;}
.hero .chain{display:flex;flex-wrap:wrap;gap:8px;margin-top:1.1rem;}
.hero .chain span{border:1px solid #3A4E7D;border-radius:999px;padding:3px 12px;font-size:.88rem;color:#E8EDF8;}
.quote{background:var(--ink2);border:1px solid #33486F;border-radius:14px;padding:18px 20px;}
.quote .q{font-family:'Martel','Noto Serif Gurmukhi',serif;font-size:1.18rem;line-height:1.55;color:#fff;margin:0;}
.quote .cap{margin:.7rem 0 0;font-size:.9rem;color:#AEBBD6;}
@media(max-width:760px){.hero{grid-template-columns:1fr;padding:22px 20px;gap:18px}}

/* ask panel */
.st-key-askpanel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px 10px;margin-top:16px;}
.panel-title{font-family:'Martel','Noto Serif Gurmukhi',serif;font-weight:700;font-size:1.3rem;color:var(--ink);margin:0 0 .2rem;}
.panel-sub{color:var(--muted);margin:0 0 .8rem;}
.stButton>button{border-radius:10px;font-family:'Mukta',sans-serif;font-weight:600;border:1px solid var(--line);background:#fff;color:var(--ink);padding:.35rem .6rem;}
.stButton>button:hover{border-color:var(--ink);color:var(--ink);}
.stButton>button[kind="primary"]{background:var(--ink);color:var(--amber);border-color:var(--ink);font-weight:800;font-size:1.08rem;padding:.65rem 1rem;}
.stButton>button[kind="primary"]:hover{background:var(--ink2);color:#fff;}
button:focus-visible,a:focus-visible,[role="tab"]:focus-visible{outline:3px solid var(--amber)!important;outline-offset:2px;}
.stTabs [data-baseweb="tab-list"]{gap:4px;border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{font-weight:600;color:var(--muted);padding:.5rem .9rem;}
.stTabs [aria-selected="true"]{color:var(--ink)!important;}
.stTabs [data-baseweb="tab-highlight"]{background:var(--amber)!important;height:3px;}
.ctx{display:inline-block;background:var(--amber-t);border:1px solid #F1D17A;border-radius:999px;padding:2px 12px;font-size:.9rem;color:#5A4300;margin:0 0 .5rem;}

/* pipeline tracker */
.pipe{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:22px 0 14px;}
.step{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;border-top:4px solid var(--ink);}
.step.skip,.step.off{border-top-color:#B8C1CE;color:var(--muted);}
.step .m{font-weight:800;color:var(--ink);font-size:1rem;}
.step.skip .m,.step.off .m{color:var(--muted);}
.step .r{font-size:.9rem;color:var(--muted);}
.step .t{font-size:.9rem;margin-top:4px;}
.step .t b{color:var(--green);}
@media(max-width:700px){.pipe{grid-template-columns:1fr}}

/* verdict + board */
.vgrid{display:grid;grid-template-columns:1.35fr 1fr;gap:14px;margin-bottom:14px;}
@media(max-width:820px){.vgrid{grid-template-columns:1fr}}
.verdict{border-radius:16px;padding:22px 24px;display:flex;gap:22px;align-items:center;border:1px solid;}
.v-sell{background:var(--red-t);border-color:#E9B4B4;--vc:var(--red);}
.v-hold{background:var(--green-t);border-color:#A9D3B9;--vc:var(--green);}
.v-none{background:var(--grey-t);border-color:var(--line);--vc:#5B6675;}
.stamp{border:4px double var(--vc);color:var(--vc);border-radius:10px;padding:10px 16px;transform:rotate(-3deg);text-align:center;flex:0 0 auto;background:rgba(255,255,255,.55);}
.stamp .en{font-family:'Martel','Noto Serif Gurmukhi',serif;font-weight:800;font-size:1.9rem;line-height:1;letter-spacing:.02em;}
.stamp .hi{font-family:'Martel','Noto Serif Gurmukhi',serif;font-weight:700;font-size:1.05rem;margin-top:4px;}
.v-body p{margin:0 0 .6rem;color:var(--text);}
.conf{font-size:.92rem;color:var(--muted);}
.conf b{color:var(--vc);}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:.2rem 0 .6rem;}
.chip{border-radius:999px;padding:2px 11px;font-size:.88rem;font-weight:600;}
.c-red{background:#F8D4D4;color:#7A1414}.c-green{background:#CDE8D7;color:#1B4D31}
.c-amber{background:#FFE7A3;color:#5A4300}.c-grey{background:#DCE2EA;color:#334155}
@media(max-width:560px){.verdict{flex-direction:column;align-items:flex-start}}
.board{background:var(--ink);color:#fff;border-radius:16px;padding:18px 22px;}
.board .row{display:flex;justify-content:space-between;gap:10px;padding:5px 0;border-bottom:1px solid #2C3F69;font-size:.98rem;}
.board .row span{color:#AEBBD6}.board .row b{font-weight:600;text-align:right}
.board .price{font-family:'Martel','Noto Serif Gurmukhi',serif;font-weight:800;font-size:2.7rem;color:var(--amber);line-height:1.1;margin:.5rem 0 0;font-variant-numeric:tabular-nums;}
.board .price small{font-family:'Mukta',sans-serif;font-weight:400;font-size:.95rem;color:#AEBBD6;margin-left:8px;}
.board .src{font-size:.85rem;color:#AEBBD6;margin:2px 0 8px;}
.board .val{display:flex;justify-content:space-between;align-items:baseline;padding-top:8px;}
.board .val b{font-family:'Martel','Noto Serif Gurmukhi',serif;font-size:1.35rem;color:#fff;}
.board .hint{font-size:.88rem;color:#AEBBD6;padding-top:8px;}

/* cards */
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:14px;}
.card h3{font-size:1.08rem;margin:0 0 .15rem;}
.card .sub{color:var(--muted);font-size:.92rem;margin:0 0 .6rem;}
.badge{display:inline-block;border-radius:6px;padding:1px 8px;font-size:.78rem;font-weight:600;margin-left:6px;vertical-align:middle;}
.b-demo{background:#FFE7A3;color:#5A4300}.b-live{background:#CDE8D7;color:#1B4D31}.b-sim{background:#E0DDF6;color:#3B2F86}
table.mt{width:100%;border-collapse:collapse;font-size:.98rem;}
table.mt th{text-align:left;font-weight:600;color:var(--muted);padding:6px 8px;border-bottom:1px solid var(--line);font-size:.9rem;}
table.mt td{padding:8px;border-bottom:1px solid #EDF0F4;font-variant-numeric:tabular-nums;}
table.mt tr.me td{background:var(--amber-t);font-weight:600;}
table.mt .pos{color:var(--green);font-weight:600}table.mt .neg{color:var(--red)}
.best{background:var(--green);color:#fff;border-radius:6px;padding:0 7px;font-size:.78rem;margin-left:6px}

/* conversation */
.convo{display:flex;flex-direction:column;gap:10px;margin:6px 0 10px;}
.bub{max-width:88%;padding:11px 15px;border-radius:14px;line-height:1.55;}
.bub small{display:block;font-size:.8rem;opacity:.75;margin-bottom:2px;font-weight:600}
.you{align-self:flex-start;background:#fff;border:1px solid var(--line);border-bottom-left-radius:4px;}
.bot{align-self:flex-end;background:var(--ink);color:#fff;border-bottom-right-radius:4px;}
.bot small{color:var(--amber);opacity:1}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 4px;}
a.btn-wa{background:#1FA855;color:#fff!important;text-decoration:none;font-weight:700;border-radius:10px;padding:.5rem 1rem;display:inline-block;}
a.btn-wa:hover{background:#188A45}

/* architecture */
.flow{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:8px 0 6px;}
.node{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--ink);border-radius:12px;padding:12px;position:relative;}
.node.gn{border-top-color:var(--amber)}
.node .n{font-weight:800;color:var(--ink)}.node .d{font-size:.88rem;color:var(--muted);margin-top:2px}
.node:not(:last-child):after{content:"›";position:absolute;right:-9px;top:50%;transform:translateY(-50%);font-size:1.5rem;color:var(--ink);font-weight:800;z-index:2}
@media(max-width:820px){.flow{grid-template-columns:1fr}.node:not(:last-child):after{content:"⌄";right:50%;top:auto;bottom:-18px;transform:translateX(50%)}}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:820px){.grid2{grid-template-columns:1fr}}
.card ul{margin:.2rem 0 0;padding-left:1.1rem}.card li{margin:.25rem 0}
code{background:#EDF0F4;border-radius:5px;padding:1px 6px;font-size:.9em}
</style>
"""

CSS = CSS.replace("</style>", """
[data-testid="stVerticalBlockBorderWrapper"]:has(.sub){background:var(--card);border-radius:14px;border-color:var(--line);}
.sub{color:var(--muted);font-size:.92rem;margin:0 0 .4rem;}
</style>""")

CSS = CSS.replace("</style>", """
.topbar-brand{font-family:'Martel','Noto Serif Gurmukhi',serif;font-weight:800;font-size:1.5rem;color:var(--ink);padding-top:.35rem}
.topbar-brand span{font-family:'Mukta',sans-serif;font-weight:600;font-size:1rem;color:var(--muted);margin-left:8px}
.hero h1{font-size:clamp(2rem,4.6vw,3.1rem)!important;line-height:1.2!important;max-width:15em}
.hero .tag{font-size:1.1rem}
.feats{display:flex;flex-wrap:wrap;gap:10px;margin-top:1.2rem}
.feats span{background:var(--ink2);border:1px solid #33486F;border-radius:10px;padding:6px 14px;font-weight:600;color:#fff;font-size:.98rem}
.feats span:before{content:"\\2713";color:var(--amber);margin-right:8px;font-weight:800}
.quote .qh{font-size:.92rem;color:var(--amber);font-weight:600;margin:0 0 .5rem}
.hint-line{color:var(--muted);font-size:.95rem;margin:.2rem 0 .6rem}
.foot{color:var(--muted);font-size:.9rem;text-align:center;margin:1.5rem 0 0}
.stamp .en{font-size:1.7rem!important}
[data-testid="stFileUploader"] section{border:2px dashed #B8C1CE;border-radius:12px;background:#F8FAFC}
[data-testid="stAudioInput"]{border-radius:12px}
</style>""")
