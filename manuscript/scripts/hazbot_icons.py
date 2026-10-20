"""Original vector engineering glyphs for HazBot; no external icon assets.

All geometry uses a 128 x 128 view box. Symbols are schematic and do not
represent as-built dimensions; the arm intentionally has three positioning
axes and a parallel gripper, matching the firmware and URDF.
"""
from html import escape

INK = '#253748'
SYMBOLS = {
'pi': '''
 <path d="M14 20 105 10l10 91-91 11Z" fill="#d8e9df"/>
 <path d="m105 10 7 5 10 91-7-5Z" fill="#a0b7aa"/>
 <path d="m24 112 91-11 7 5-91 11Z" fill="#7f9c8d"/>
 <path d="m22 32 23-3 2 18-23 3Z" fill="#c2d2db"/>
 <path d="m23 34 19-2 1 11-19 2Z" fill="#516879"/>
 <path d="m26 61 14-2 3 23-14 2Z" fill="#b6c8d1"/>
 <path d="m27 65 7-1 2 13-7 1Z" fill="#536a79"/>
 <path d="m52 40 28-3 4 30-28 3Z" fill="#354a57"/>
 <path d="m58 46 17-2 2 17-17 2Z" fill="#697d88"/>
 <path d="m58 33 0 6m8-7 0 6m8-7 0 6M59 71l1 6m8-7 1 6m8-7 1 6M49 47l6-1m-5 10 6-1m26-10 6-1m-5 10 6-1" stroke="#668b78"/>
 <path d="m52 17 44-5 2 9-44 5Z" fill="#334a3c"/>
 <path d="m57 18 1 5m5-6 1 5m5-6 1 5m5-6 1 5m5-6 1 5m5-6 1 5" stroke="#d6c294" stroke-width="2.4"/>
 <path d="m91 36 17-2 2 18-17 2Z m3 27 17-2 2 18-17 2Z" fill="#b9c8cf"/>
 <path d="m96 39 10-1 1 8-10 1Z m3 27 10-1 1 8-10 1Z" fill="#536a79"/>
 <path d="m45 91 27-3 1 9-27 3Z" fill="#f7faf8"/>
 <path d="m76 86 9-1 1 14-9 1Z" fill="#7f9c8d"/>
 <circle cx="28" cy="26" r="3.3" fill="#fafcfb"/><circle cx="104" cy="92" r="3.3" fill="#fafcfb"/>
 <circle cx="41" cy="94" r="2.2" fill="#d39336" stroke="none"/>
''',
'camera': '''
 <path d="m20 31 74-8 8 65-74 8Z" fill="#d5e6db"/>
 <path d="m94 23 8 5 8 65-8-5Z" fill="#90aa9a"/>
 <path d="m28 96 74-8 8 5-74 8Z" fill="#a8beb1"/>
 <path d="m41 42 39-4 4 36-39 4Z" fill="#52636d"/>
 <ellipse cx="63" cy="57" rx="18" ry="19" fill="#f6fafc"/>
 <ellipse cx="63" cy="57" rx="13" ry="14" fill="#4a6d81"/>
 <ellipse cx="63" cy="57" rx="8" ry="9" fill="#244052"/>
 <circle cx="59" cy="53" r="3.8" fill="#a9cbd9" stroke="none"/>
 <circle cx="29" cy="38" r="3" fill="#f9fcfa"/><circle cx="93" cy="81" r="3" fill="#f9fcfa"/>
 <path d="m40 89 35-4 2 10-35 4Z" fill="#e8d7b3"/>
 <path d="m45 98 4 22h25l-2-25" fill="#e9d9b5"/>
 <path d="m53 98 3 20m6-21 2 21" stroke="#baa982"/>
''',
'lidar': '''
 <ellipse cx="65" cy="96" rx="42" ry="14" fill="#b7c4cd"/>
 <path d="M23 74v22c0 19 84 19 84 0V74Z" fill="#cbd5dc"/>
 <ellipse cx="65" cy="74" rx="42" ry="14" fill="#f7fafb"/>
 <path d="M31 49v25c0 18 68 18 68 0V49Z" fill="#bd6259"/>
 <ellipse cx="65" cy="49" rx="34" ry="12" fill="#e0b1a7"/>
 <path d="M37 59v13c14 7 43 7 56 0V59c-16 7-41 7-56 0Z" fill="#445663"/>
 <path d="M65 30V12M38 35 26 20M92 35l12-15M25 48 8 42m96 6 16-6" stroke="#a24f48" stroke-width="2"/>
 <circle cx="65" cy="48" r="6" fill="#bb6259"/>
 <path d="M46 88h38M48 99h34" stroke="#758d9d"/>
''',
'arduino': '''
 <path d="m16 21 88-7 10 84-88 8Z" fill="#c6e5e7"/>
 <path d="m104 14 7 5 10 84-7-5Z" fill="#88b8bb"/>
 <path d="m26 106 88-8 7 5-88 8Z" fill="#7fabad"/>
 <path d="m43 44 40-4 4 29-40 4Z" fill="#425868"/>
 <path d="m47 38 1 6m9-7 1 6m9-7 1 6m9-7 1 6M51 74l1 6m9-7 1 6m9-7 1 6m9-7 1 6"/>
 <path d="m10 30 25-2 2 23-25 2Z" fill="#d1dae0"/>
 <path d="m12 35 14-1 1 11-14 1Z" fill="#637988"/>
 <path d="m35 21 62-5 1 8-62 5Z m5 71 57-5 1 8-57 5Z" fill="#45616c"/>
 <path d="m40 23 0 3m7-4 0 3m7-4 0 3m7-4 0 3m7-4 0 3m7-4 0 3m7-4 0 3m7-4 0 3M45 95v3m7-4v3m7-4v3m7-4v3m7-4v3m7-4v3m7-4v3" stroke="#dfc28e"/>
 <circle cx="32" cy="88" r="3" fill="#f4fbfb"/><circle cx="101" cy="86" r="3" fill="#f4fbfb"/>
 <circle cx="92" cy="33" r="2.5" fill="#ad8c39" stroke="none"/>
''',
'controller': '''
 <path d="m25 32 74-8 8 70-74 8Z" fill="#c8e2e6"/>
 <path d="m99 24 7 4 8 70-7-4Z" fill="#8ab0b8"/>
 <path d="m46 43 30-3 4 32-30 3Z" fill="#3d596d"/>
 <path d="m43 50 6-1m-5 10 6-1m29-12 6-1m-5 10 6-1M56 36v6m9-7v6m-6 33v6m9-7v6"/>
 <path d="m30 24 28-3 1 12-28 3Z m15 58 26-3 1 10-26 3Z" fill="#e4edf1"/>
 <path d="m57 98 3 17h15l-2-19" fill="#b6c5ce"/>
 <path d="M63 115v10m6-10v10"/>
''',
'driver': '''
 <path d="m15 42 91-10 9 67-91 10Z" fill="#e5beb5"/>
 <path d="m106 32 7 4 9 67-7-4Z" fill="#ba877c"/>
 <path d="m37 24 48-5 6 54-48 5Z" fill="#7b8b97"/>
 <path d="m43 24 6 53m4-54 6 53m4-54 6 53m4-54 6 53" stroke="#3d515e" stroke-width="3"/>
 <path d="m25 89 27-3 2 17-27 3Z m45-22 27-3 2 17-27 3Z" fill="#a5c8d0"/>
 <path d="m32 94 0 5m9-6 0 5m36-8 0 5m9-6 0 5" stroke="#425a68"/>
 <path d="m19 58 12-1 1 14-12 1Z" fill="#d2dbe0"/>
''',
'drive': '''
 <path d="m40 30 49-5 10 69-49 6Z" fill="#d5dfe5"/>
 <path d="m40 30 14 9 49-6-14-8Z" fill="#edf2f5"/>
 <path d="m89 25 14 8 10 69-14-8Z" fill="#acbcc8"/>
 <path d="M13 43c0-12 23-14 29-4l7 53c1 13-21 17-28 6Z" fill="#55626d"/>
 <path d="m17 47 25-4m-24 15 25-4m-24 15 25-4m-24 15 25-4m-24 15 25-4" stroke="#a5b1ba"/>
 <path d="M90 35c0-12 22-14 27-3l7 52c1 13-20 16-27 6Z" fill="#55626d"/>
 <path d="m94 39 23-4m-22 15 23-4m-22 15 23-4m-22 15 23-4m-22 15 23-4" stroke="#a5b1ba"/>
 <path d="m62 82-4-30m-5 8 5-8 7 6" stroke="#337ca0" stroke-width="2.5" fill="none"/>
''',
'arm': '''
 <ellipse cx="35" cy="111" rx="26" ry="9" fill="#b9c8d2"/>
 <path d="M9 102v9c0 12 52 12 52 0v-9Z" fill="#a3b7c4"/>
 <ellipse cx="35" cy="102" rx="26" ry="9" fill="#e2e9ee"/>
 <path d="M22 91h26v12H22Z" fill="#4e697f"/>
 <path d="m25 84 27-59 13 6-26 59Z" fill="#bfcdd7"/>
 <path d="m31 84 28-57" fill="none" stroke="#edf4f6" stroke-width="4"/>
 <path d="m59 20 44 31-8 14-45-32Z" fill="#c6d2db"/>
 <path d="m61 25 36 27" stroke="#edf4f6" stroke-width="4"/>
 <circle cx="33" cy="86" r="13" fill="#5b7e97"/><circle cx="33" cy="86" r="6" fill="#d6e1e8"/>
 <circle cx="58" cy="27" r="12" fill="#5b7e97"/><circle cx="58" cy="27" r="5" fill="#d6e1e8"/>
 <path d="m96 49 15 11-6 10-15-10Z" fill="#5b6e7e"/>
 <path d="m107 64 13 5-1 21-8 4-4-7m-5-19-7 12 10 19 8-1" fill="none" stroke="#b9863c" stroke-width="5"/>
 <path d="M19 86 45 30M46 25l48 27" stroke="#596b78" stroke-width="1.3" stroke-dasharray="3 3" fill="none"/>
''',

'joint': '''<circle cx="64" cy="64" r="56" fill="#587d96"/><circle cx="64" cy="64" r="34" fill="#d4e0e8"/><circle cx="64" cy="64" r="12" fill="#7c98aa"/>''',
'pedestal': '''<ellipse cx="64" cy="99" rx="52" ry="18" fill="#adc1cd"/><path d="M12 78v21c0 23 104 23 104 0V78Z" fill="#b7cbd6"/><ellipse cx="64" cy="78" rx="52" ry="18" fill="#e1e9ee"/><path d="M41 29h46v44H41Z" fill="#5b7f96"/><path d="M35 29h58v10H35Z" fill="#a8becd"/>''',
'container': '''
 <path d="m20 48 70-12 20 13-70 12Z" fill="#f2e8ce"/>
 <path d="m40 61 70-12v53l-70 12Z" fill="#d4c6a0"/>
 <path d="m20 48 20 13v53l-20-14Z" fill="#baac89"/>
 <path d="m29 46 57-9 13 9-57 9Z" fill="#6d7165"/>
 <path d="m61 67 26-4v20l-26 4Z" fill="#f8f5eb"/>
 <path d="m71 69v9m-4-4h8" stroke="#83764d"/>
''',
'object': '''
 <path d="m33 39 43-7 23 15-43 8Z" fill="#d7e7ed"/>
 <path d="m56 55 43-8v41l-43 9Z" fill="#9abacb"/>
 <path d="m33 39 23 16v42L33 81Z" fill="#7695aa"/>
 <path d="m54 46 20-4 9 6-20 4Z" fill="#f6f9fb"/>
''',
}


def svg_symbols():
    return '<defs>'+''.join(f'<symbol id="hazbot-{escape(name)}" viewBox="0 0 128 128"><g stroke="{INK}" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round">{geometry}</g></symbol>' for name,geometry in SYMBOLS.items())+'</defs>'


def icon_use(name, x, y, width=100, height=None):
    if name not in SYMBOLS:
        raise KeyError(name)
    height = width if height is None else height
    return f'<use href="#hazbot-{escape(name)}" x="{x}" y="{y}" width="{width}" height="{height}"/>'
