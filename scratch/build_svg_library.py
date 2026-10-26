# -*- coding: utf-8 -*-
"""
SVG Library Generator for FT Visual Vocabulary (73) and 60 Ways to Visualize Time (60).
All SVGs strictly adhere to Edward Tufte's Data-Ink ratio:
- 200x120 viewBox
- Clean vector geometry, crisp line weights (1.5-2.5px)
- Muted background guides, zero decorative drop shadows, zero 3D
- Distinct semantic palette: #2563EB (Actual), #64748B (Budget/Neutral), #EF4444 (Merforbruk), #10B981 (Mindreforbruk), #F59E0B (EAC/Warning)
"""
import json

FT_SVGS = {
    # Ordered Proportional Symbol
    "ft_rnk_3": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="60" x2="180" y2="60" stroke="var(--border)" stroke-width="1.5"/>
        <circle cx="45" cy="60" r="24" fill="#2563EB" fill-opacity="0.25" stroke="#2563EB" stroke-width="2"/>
        <circle cx="95" cy="60" r="16" fill="#3B82F6" fill-opacity="0.25" stroke="#3B82F6" stroke-width="2"/>
        <circle cx="135" cy="60" r="11" fill="#60A5FA" fill-opacity="0.25" stroke="#60A5FA" stroke-width="1.5"/>
        <circle cx="165" cy="60" r="7" fill="#93C5FD" fill-opacity="0.25" stroke="#93C5FD" stroke-width="1.5"/>
        <text x="45" y="64" font-size="9" font-weight="700" text-anchor="middle" fill="var(--text)">6.2M</text>
        <text x="95" y="64" font-size="8" font-weight="700" text-anchor="middle" fill="var(--text)">1.5M</text>
    </svg>''',

    # Dot Strip Plot (Ranking)
    "ft_rnk_4": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="30" y1="30" x2="180" y2="30" stroke="var(--border)" stroke-width="1"/>
        <line x1="30" y1="60" x2="180" y2="60" stroke="var(--border)" stroke-width="1"/>
        <line x1="30" y1="90" x2="180" y2="90" stroke="var(--border)" stroke-width="1"/>
        <circle cx="50" cy="30" r="4.5" fill="#2563EB" opacity="0.8"/>
        <circle cx="65" cy="30" r="4.5" fill="#2563EB" opacity="0.8"/>
        <circle cx="120" cy="30" r="4.5" fill="#2563EB" opacity="0.8"/>
        <circle cx="165" cy="30" r="5" fill="#EF4444"/>
        <circle cx="40" cy="60" r="4.5" fill="#2563EB" opacity="0.8"/>
        <circle cx="85" cy="60" r="4.5" fill="#2563EB" opacity="0.8"/>
        <circle cx="95" cy="60" r="4.5" fill="#2563EB" opacity="0.8"/>
        <circle cx="140" cy="60" r="4.5" fill="#2563EB" opacity="0.8"/>
        <circle cx="60" cy="90" r="4.5" fill="#2563EB" opacity="0.8"/>
        <circle cx="70" cy="90" r="4.5" fill="#2563EB" opacity="0.8"/>
        <circle cx="110" cy="90" r="4.5" fill="#2563EB" opacity="0.8"/>
        <circle cx="150" cy="90" r="5" fill="#EF4444"/>
    </svg>''',

    # Dot Plot (Distribution)
    "ft_dst_2": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="90" x2="175" y2="90" stroke="var(--border-strong)" stroke-width="1.5"/>
        <circle cx="45" cy="90" r="5" fill="#10B981"/>
        <circle cx="70" cy="90" r="5" fill="#3B82F6"/>
        <circle cx="75" cy="80" r="5" fill="#3B82F6"/>
        <circle cx="95" cy="90" r="5" fill="#3B82F6"/>
        <circle cx="100" cy="80" r="5" fill="#3B82F6"/>
        <circle cx="100" cy="70" r="5" fill="#3B82F6"/>
        <circle cx="125" cy="90" r="5" fill="#3B82F6"/>
        <circle cx="155" cy="90" r="5" fill="#EF4444"/>
        <text x="25" y="108" font-size="9" fill="var(--text-dim)">Min (0)</text>
        <text x="175" y="108" font-size="9" text-anchor="end" fill="var(--text-dim)">Maks (500k)</text>
    </svg>''',

    # Dot Strip Plot (Distribution)
    "ft_dst_3": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="60" x2="175" y2="60" stroke="var(--border)" stroke-width="1.5"/>
        <circle cx="40" cy="60" r="5" fill="#3B82F6" opacity="0.6"/>
        <circle cx="48" cy="54" r="5" fill="#3B82F6" opacity="0.6"/>
        <circle cx="52" cy="66" r="5" fill="#3B82F6" opacity="0.6"/>
        <circle cx="75" cy="60" r="5" fill="#3B82F6" opacity="0.6"/>
        <circle cx="82" cy="52" r="5" fill="#3B82F6" opacity="0.6"/>
        <circle cx="85" cy="64" r="5" fill="#3B82F6" opacity="0.6"/>
        <circle cx="90" cy="58" r="5" fill="#3B82F6" opacity="0.6"/>
        <circle cx="115" cy="60" r="5" fill="#3B82F6" opacity="0.6"/>
        <circle cx="145" cy="60" r="5" fill="#3B82F6" opacity="0.6"/>
        <circle cx="165" cy="60" r="6" fill="#EF4444"/>
    </svg>''',

    # Barcode Plot
    "ft_dst_4": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="60" x2="175" y2="60" stroke="var(--border)" stroke-width="1"/>
        <line x1="35" y1="35" x2="35" y2="85" stroke="#3B82F6" stroke-width="2"/>
        <line x1="42" y1="40" x2="42" y2="80" stroke="#3B82F6" stroke-width="1.5"/>
        <line x1="50" y1="35" x2="50" y2="85" stroke="#3B82F6" stroke-width="2"/>
        <line x1="55" y1="38" x2="55" y2="82" stroke="#3B82F6" stroke-width="1.5"/>
        <line x1="58" y1="35" x2="58" y2="85" stroke="#3B82F6" stroke-width="2"/>
        <line x1="68" y1="40" x2="68" y2="80" stroke="#3B82F6" stroke-width="1.5"/>
        <line x1="80" y1="35" x2="80" y2="85" stroke="#3B82F6" stroke-width="2"/>
        <line x1="95" y1="35" x2="95" y2="85" stroke="#3B82F6" stroke-width="2"/>
        <line x1="110" y1="38" x2="110" y2="82" stroke="#3B82F6" stroke-width="1.5"/>
        <line x1="135" y1="40" x2="135" y2="80" stroke="#3B82F6" stroke-width="1.5"/>
        <line x1="165" y1="25" x2="165" y2="95" stroke="#EF4444" stroke-width="3"/>
        <text x="165" y="19" font-size="9" font-weight="700" text-anchor="middle" fill="#EF4444">Outlier</text>
    </svg>''',

    # Population Pyramid
    "ft_dst_7": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="100" y1="15" x2="100" y2="105" stroke="var(--border-strong)" stroke-width="1.5"/>
        <rect x="55" y="25" width="45" height="12" fill="#2563EB" rx="1"/>
        <rect x="100" y="25" width="30" height="12" fill="#EF4444" rx="1"/>
        <rect x="40" y="42" width="60" height="12" fill="#2563EB" rx="1"/>
        <rect x="100" y="42" width="48" height="12" fill="#EF4444" rx="1"/>
        <rect x="30" y="59" width="70" height="12" fill="#2563EB" rx="1"/>
        <rect x="100" y="59" width="55" height="12" fill="#EF4444" rx="1"/>
        <rect x="50" y="76" width="50" height="12" fill="#2563EB" rx="1"/>
        <rect x="100" y="76" width="35" height="12" fill="#EF4444" rx="1"/>
        <text x="75" y="103" font-size="8" text-anchor="middle" fill="#2563EB">Fast</text>
        <text x="125" y="103" font-size="8" text-anchor="middle" fill="#EF4444">Vikar</text>
    </svg>''',

    # Cumulative Curve (Lorenz)
    "ft_dst_8": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <rect x="35" y="15" width="130" height="85" fill="none" stroke="var(--border)" stroke-width="1"/>
        <line x1="35" y1="100" x2="165" y2="15" stroke="var(--border-strong)" stroke-width="1.5" stroke-dasharray="3 3"/>
        <path d="M 35 100 Q 110 95, 140 50 T 165 15" fill="none" stroke="#2563EB" stroke-width="2.5"/>
        <circle cx="140" cy="50" r="4" fill="#EF4444"/>
        <text x="135" y="42" font-size="8" font-weight="700" text-anchor="end" fill="#EF4444">80/20 Pareto</text>
    </svg>''',

    # Frequency Polygons
    "ft_dst_9": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="100" x2="175" y2="100" stroke="var(--border)" stroke-width="1"/>
        <polygon points="35,100 60,65 90,25 120,55 145,85 165,100" fill="#2563EB" fill-opacity="0.2" stroke="#2563EB" stroke-width="2"/>
        <polygon points="35,100 55,85 85,50 115,20 145,45 165,100" fill="#F59E0B" fill-opacity="0.15" stroke="#F59E0B" stroke-width="2" stroke-dasharray="3 2"/>
    </svg>''',

    # Beeswarm Plot
    "ft_dst_10": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="60" x2="175" y2="60" stroke="var(--border)" stroke-width="1"/>
        <circle cx="45" cy="60" r="4" fill="#3B82F6"/>
        <circle cx="53" cy="54" r="4" fill="#3B82F6"/>
        <circle cx="53" cy="66" r="4" fill="#3B82F6"/>
        <circle cx="75" cy="60" r="4" fill="#3B82F6"/>
        <circle cx="82" cy="52" r="4" fill="#3B82F6"/>
        <circle cx="82" cy="68" r="4" fill="#3B82F6"/>
        <circle cx="89" cy="45" r="4" fill="#3B82F6"/>
        <circle cx="89" cy="60" r="4" fill="#3B82F6"/>
        <circle cx="89" cy="75" r="4" fill="#3B82F6"/>
        <circle cx="96" cy="53" r="4" fill="#3B82F6"/>
        <circle cx="96" cy="67" r="4" fill="#3B82F6"/>
        <circle cx="120" cy="60" r="4" fill="#3B82F6"/>
        <circle cx="150" cy="60" r="4.5" fill="#EF4444"/>
        <circle cx="168" cy="60" r="5" fill="#EF4444"/>
    </svg>''',

    # Column Chart (Time)
    "ft_tim_2": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <rect x="30" y="45" width="12" height="55" fill="#2563EB" rx="1"/>
        <rect x="48" y="30" width="12" height="70" fill="#2563EB" rx="1"/>
        <rect x="66" y="50" width="12" height="50" fill="#2563EB" rx="1"/>
        <rect x="84" y="25" width="12" height="75" fill="#2563EB" rx="1"/>
        <rect x="102" y="40" width="12" height="60" fill="#2563EB" rx="1"/>
        <rect x="120" y="65" width="12" height="35" fill="#2563EB" rx="1"/>
        <rect x="138" y="20" width="12" height="80" fill="#EF4444" rx="1"/>
        <rect x="156" y="28" width="12" height="72" fill="#EF4444" rx="1"/>
    </svg>''',

    # Column + Line Timeline
    "ft_tim_3": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1"/>
        <rect x="30" y="55" width="14" height="45" fill="#94A3B8" opacity="0.4" rx="1"/>
        <rect x="52" y="35" width="14" height="65" fill="#94A3B8" opacity="0.4" rx="1"/>
        <rect x="74" y="45" width="14" height="55" fill="#94A3B8" opacity="0.4" rx="1"/>
        <rect x="96" y="25" width="14" height="75" fill="#94A3B8" opacity="0.4" rx="1"/>
        <rect x="118" y="40" width="14" height="60" fill="#94A3B8" opacity="0.4" rx="1"/>
        <rect x="140" y="20" width="14" height="80" fill="#EF4444" opacity="0.6" rx="1"/>
        <path d="M 37 50 L 59 45 L 81 48 L 103 40 L 125 42 L 147 40" fill="none" stroke="#2563EB" stroke-width="2.5"/>
        <circle cx="147" cy="40" r="3.5" fill="#2563EB"/>
    </svg>''',

    # Area Chart (Time)
    "ft_tim_5": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1"/>
        <polygon points="30,100 30,70 60,45 90,60 120,30 150,45 175,20 175,100" fill="#2563EB" fill-opacity="0.2"/>
        <path d="M 30 70 L 60 45 L 90 60 L 120 30 L 150 45 L 175 20" fill="none" stroke="#2563EB" stroke-width="2.5"/>
        <circle cx="175" cy="20" r="3.5" fill="#2563EB"/>
    </svg>''',

    # Connected Scatterplot (Time)
    "ft_tim_7": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="105" x2="175" y2="105" stroke="var(--border)" stroke-width="1"/>
        <line x1="25" y1="15" x2="25" y2="105" stroke="var(--border)" stroke-width="1"/>
        <path d="M 40 85 L 65 50 L 100 35 L 130 65 L 155 40" fill="none" stroke="#2563EB" stroke-width="2"/>
        <circle cx="40" cy="85" r="4" fill="#2563EB"/>
        <circle cx="65" cy="50" r="4" fill="#2563EB"/>
        <circle cx="100" cy="35" r="4" fill="#2563EB"/>
        <circle cx="130" cy="65" r="4" fill="#2563EB"/>
        <circle cx="155" cy="40" r="5" fill="#EF4444"/>
        <text x="40" y="97" font-size="8" fill="var(--text-dim)">P01</text>
        <text x="155" y="32" font-size="8" font-weight="700" fill="#EF4444">P08</text>
    </svg>''',

    # Priestley Timeline
    "ft_tim_9": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="100" x2="175" y2="100" stroke="var(--border)" stroke-width="1"/>
        <rect x="35" y="25" width="60" height="10" fill="#3B82F6" rx="2"/>
        <rect x="80" y="42" width="75" height="10" fill="#2563EB" rx="2"/>
        <rect x="50" y="59" width="45" height="10" fill="#60A5FA" rx="2"/>
        <rect x="115" y="76" width="55" height="10" fill="#EF4444" rx="2"/>
        <line x1="125" y1="15" x2="125" y2="100" stroke="#F59E0B" stroke-width="1.5" stroke-dasharray="3 2"/>
        <text x="125" y="12" font-size="8" font-weight="700" text-anchor="middle" fill="#F59E0B">Nå</text>
    </svg>''',

    # Vertical Timeline
    "ft_tim_11": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="100" y1="15" x2="100" y2="105" stroke="var(--border-strong)" stroke-width="2"/>
        <circle cx="100" cy="30" r="4" fill="#2563EB"/>
        <rect x="112" y="24" width="55" height="12" fill="#2563EB" fill-opacity="0.2" rx="2"/>
        <circle cx="100" cy="55" r="4" fill="#2563EB"/>
        <rect x="33" y="49" width="55" height="12" fill="#2563EB" fill-opacity="0.2" rx="2"/>
        <circle cx="100" cy="80" r="4" fill="#EF4444"/>
        <rect x="112" y="74" width="55" height="12" fill="#EF4444" fill-opacity="0.2" rx="2"/>
    </svg>''',

    # Seismogram
    "ft_tim_12": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="60" x2="180" y2="60" stroke="var(--border)" stroke-width="1"/>
        <path d="M 25 60 L 40 58 L 50 63 L 60 55 L 70 65 L 80 40 L 85 85 L 90 25 L 95 95 L 100 50 L 110 65 L 125 57 L 140 75 L 145 35 L 150 80 L 160 58 L 175 60" fill="none" stroke="#EF4444" stroke-width="1.5"/>
    </svg>''',

    # Streamgraph
    "ft_tim_13": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <path d="M 25 60 C 50 45, 90 35, 120 45 C 150 55, 165 50, 175 60 C 165 70, 150 65, 120 75 C 90 85, 50 75, 25 60 Z" fill="#2563EB" fill-opacity="0.4"/>
        <path d="M 25 60 C 50 50, 90 45, 120 52 C 150 60, 165 55, 175 60 C 165 65, 150 60, 120 68 C 90 75, 50 70, 25 60 Z" fill="#10B981" fill-opacity="0.5"/>
        <path d="M 25 60 C 50 55, 90 52, 120 57 C 150 62, 165 58, 175 60 C 165 62, 150 58, 120 63 C 90 68, 50 65, 25 60 Z" fill="#F59E0B" fill-opacity="0.6"/>
    </svg>''',

    # Paired Column Chart (Magnitude)
    "ft_mag_3": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1"/>
        <rect x="35" y="40" width="12" height="60" fill="#64748B" rx="1"/>
        <rect x="49" y="25" width="12" height="75" fill="#2563EB" rx="1"/>
        <rect x="80" y="55" width="12" height="45" fill="#64748B" rx="1"/>
        <rect x="94" y="50" width="12" height="50" fill="#2563EB" rx="1"/>
        <rect x="125" y="65" width="12" height="35" fill="#64748B" rx="1"/>
        <rect x="139" y="30" width="12" height="70" fill="#EF4444" rx="1"/>
    </svg>''',

    # Paired Bar Chart
    "ft_mag_4": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="30" y1="15" x2="30" y2="105" stroke="var(--border)" stroke-width="1"/>
        <rect x="30" y="25" width="85" height="10" fill="#64748B" rx="1"/>
        <rect x="30" y="37" width="115" height="10" fill="#2563EB" rx="1"/>
        <rect x="30" y="60" width="60" height="10" fill="#64748B" rx="1"/>
        <rect x="30" y="72" width="90" height="10" fill="#EF4444" rx="1"/>
    </svg>''',

    # Marimekko (Mekko)
    "ft_mag_5": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <rect x="25" y="20" width="85" height="50" fill="#2563EB" stroke="var(--card-bg)" stroke-width="2"/>
        <rect x="25" y="70" width="85" height="30" fill="#3B82F6" stroke="var(--card-bg)" stroke-width="2"/>
        <rect x="110" y="20" width="45" height="40" fill="#F59E0B" stroke="var(--card-bg)" stroke-width="2"/>
        <rect x="110" y="60" width="45" height="40" fill="#FBBF24" stroke="var(--card-bg)" stroke-width="2"/>
        <rect x="155" y="20" width="25" height="80" fill="#EF4444" stroke="var(--card-bg)" stroke-width="2"/>
    </svg>''',

    # Proportional Symbol
    "ft_mag_6": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <circle cx="60" cy="60" r="32" fill="#2563EB" fill-opacity="0.3" stroke="#2563EB" stroke-width="2"/>
        <circle cx="125" cy="55" r="22" fill="#10B981" fill-opacity="0.3" stroke="#10B981" stroke-width="2"/>
        <circle cx="165" cy="70" r="14" fill="#EF4444" fill-opacity="0.3" stroke="#EF4444" stroke-width="2"/>
        <text x="60" y="64" font-size="10" font-weight="700" text-anchor="middle" fill="var(--text)">Lønn</text>
    </svg>''',

    # Isotype / Pictogram
    "ft_mag_7": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <g fill="#2563EB">
            <rect x="35" y="30" width="10" height="14" rx="2"/><rect x="50" y="30" width="10" height="14" rx="2"/>
            <rect x="65" y="30" width="10" height="14" rx="2"/><rect x="80" y="30" width="10" height="14" rx="2"/>
            <rect x="95" y="30" width="10" height="14" rx="2"/><rect x="110" y="30" width="10" height="14" rx="2"/>
        </g>
        <g fill="#EF4444">
            <rect x="35" y="55" width="10" height="14" rx="2"/><rect x="50" y="55" width="10" height="14" rx="2"/>
            <rect x="65" y="55" width="10" height="14" rx="2"/><rect x="80" y="55" width="10" height="14" rx="2"/>
        </g>
        <text x="135" y="42" font-size="10" font-weight="600" fill="var(--text)">Fast ansatte (18)</text>
        <text x="105" y="67" font-size="10" font-weight="600" fill="#EF4444">Vikarer (12)</text>
    </svg>''',

    # Parallel Coordinates
    "ft_mag_10": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="35" y1="20" x2="35" y2="100" stroke="var(--border-strong)" stroke-width="1"/>
        <line x1="75" y1="20" x2="75" y2="100" stroke="var(--border-strong)" stroke-width="1"/>
        <line x1="115" y1="20" x2="115" y2="100" stroke="var(--border-strong)" stroke-width="1"/>
        <line x1="155" y1="20" x2="155" y2="100" stroke="var(--border-strong)" stroke-width="1"/>
        <polyline points="35,30 75,65 115,40 155,80" fill="none" stroke="#2563EB" stroke-width="2"/>
        <polyline points="35,80 75,40 115,85 155,25" fill="none" stroke="#EF4444" stroke-width="2.5"/>
        <polyline points="35,50 75,75 115,60 155,55" fill="none" stroke="#94A3B8" stroke-width="1.5"/>
    </svg>''',

    # Grouped Symbol
    "ft_mag_12": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <circle cx="55" cy="50" r="14" fill="#3B82F6" opacity="0.7"/>
        <circle cx="75" cy="65" r="18" fill="#3B82F6" opacity="0.7"/>
        <circle cx="50" cy="75" r="10" fill="#3B82F6" opacity="0.7"/>
        <circle cx="135" cy="45" r="16" fill="#F59E0B" opacity="0.7"/>
        <circle cx="155" cy="65" r="22" fill="#EF4444" opacity="0.7"/>
    </svg>''',

    # Stacked Column / Bar
    "ft_ptw_1": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1"/>
        <rect x="45" y="65" width="28" height="35" fill="#2563EB"/>
        <rect x="45" y="45" width="28" height="20" fill="#3B82F6"/>
        <rect x="45" y="30" width="28" height="15" fill="#EF4444"/>
        <rect x="105" y="55" width="28" height="45" fill="#2563EB"/>
        <rect x="105" y="35" width="28" height="20" fill="#3B82F6"/>
        <rect x="105" y="15" width="28" height="20" fill="#EF4444"/>
    </svg>''',

    # Pie Chart
    "ft_ptw_3": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="60" r="42" fill="#2563EB"/>
        <path d="M 100 60 L 100 18 A 42 42 0 0 1 142 60 Z" fill="#EF4444"/>
        <path d="M 100 60 L 142 60 A 42 42 0 0 1 125 96 Z" fill="#F59E0B"/>
        <path d="M 100 60 L 125 96 A 42 42 0 0 1 100 102 Z" fill="#10B981"/>
    </svg>''',

    # Voronoi Diagram
    "ft_ptw_6": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <polygon points="25,20 85,20 75,60 30,70" fill="#2563EB" fill-opacity="0.3" stroke="var(--card-bg)" stroke-width="2"/>
        <polygon points="85,20 155,20 140,55 75,60" fill="#3B82F6" fill-opacity="0.3" stroke="var(--card-bg)" stroke-width="2"/>
        <polygon points="155,20 175,20 175,70 140,55" fill="#F59E0B" fill-opacity="0.3" stroke="var(--card-bg)" stroke-width="2"/>
        <polygon points="30,70 75,60 95,100 25,100" fill="#10B981" fill-opacity="0.3" stroke="var(--card-bg)" stroke-width="2"/>
        <polygon points="75,60 140,55 160,100 95,100" fill="#EF4444" fill-opacity="0.3" stroke="var(--card-bg)" stroke-width="2"/>
        <polygon points="140,55 175,70 175,100 160,100" fill="#8B5CF6" fill-opacity="0.3" stroke="var(--card-bg)" stroke-width="2"/>
    </svg>''',

    # Arc (Hemicycle)
    "ft_ptw_7": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <path d="M 40 90 A 60 60 0 0 1 160 90" fill="none" stroke="var(--border)" stroke-width="12"/>
        <path d="M 40 90 A 60 60 0 0 1 130 38" fill="none" stroke="#2563EB" stroke-width="12"/>
        <path d="M 130 38 A 60 60 0 0 1 160 90" fill="none" stroke="#EF4444" stroke-width="12"/>
        <text x="100" y="85" font-size="12" font-weight="700" text-anchor="middle" fill="var(--text)">73% / 27%</text>
    </svg>''',

    # Gridplot (Waffle Chart)
    "ft_ptw_8": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <g transform="translate(60, 20)">
            <!-- 5x5 waffle sample -->
            <rect x="0" y="0" width="12" height="12" rx="2" fill="#2563EB"/><rect x="16" y="0" width="12" height="12" rx="2" fill="#2563EB"/><rect x="32" y="0" width="12" height="12" rx="2" fill="#2563EB"/><rect x="48" y="0" width="12" height="12" rx="2" fill="#2563EB"/><rect x="64" y="0" width="12" height="12" rx="2" fill="#EF4444"/>
            <rect x="0" y="16" width="12" height="12" rx="2" fill="#2563EB"/><rect x="16" y="16" width="12" height="12" rx="2" fill="#2563EB"/><rect x="32" y="16" width="12" height="12" rx="2" fill="#2563EB"/><rect x="48" y="16" width="12" height="12" rx="2" fill="#2563EB"/><rect x="64" y="16" width="12" height="12" rx="2" fill="#EF4444"/>
            <rect x="0" y="32" width="12" height="12" rx="2" fill="#2563EB"/><rect x="16" y="32" width="12" height="12" rx="2" fill="#2563EB"/><rect x="32" y="32" width="12" height="12" rx="2" fill="#2563EB"/><rect x="48" y="32" width="12" height="12" rx="2" fill="#2563EB"/><rect x="64" y="32" width="12" height="12" rx="2" fill="#EF4444"/>
            <rect x="0" y="48" width="12" height="12" rx="2" fill="#2563EB"/><rect x="16" y="48" width="12" height="12" rx="2" fill="#2563EB"/><rect x="32" y="48" width="12" height="12" rx="2" fill="#2563EB"/><rect x="48" y="48" width="12" height="12" rx="2" fill="#94A3B8"/><rect x="64" y="48" width="12" height="12" rx="2" fill="#94A3B8"/>
            <rect x="0" y="64" width="12" height="12" rx="2" fill="#2563EB"/><rect x="16" y="64" width="12" height="12" rx="2" fill="#2563EB"/><rect x="32" y="64" width="12" height="12" rx="2" fill="#94A3B8"/><rect x="48" y="64" width="12" height="12" rx="2" fill="#94A3B8"/><rect x="64" y="64" width="12" height="12" rx="2" fill="#94A3B8"/>
        </g>
    </svg>''',

    # Venn Diagram
    "ft_ptw_9": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <circle cx="80" cy="60" r="35" fill="#2563EB" fill-opacity="0.3" stroke="#2563EB" stroke-width="2"/>
        <circle cx="120" cy="60" r="35" fill="#EF4444" fill-opacity="0.3" stroke="#EF4444" stroke-width="2"/>
        <text x="65" y="64" font-size="9" fill="var(--text)">Overtid</text>
        <text x="135" y="64" font-size="9" fill="var(--text)">Vikar</text>
    </svg>''',

    # Chord Diagram
    "ft_flw_3": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="60" r="42" fill="none" stroke="var(--border)" stroke-width="3"/>
        <path d="M 70 30 Q 100 60, 130 90" fill="none" stroke="#2563EB" stroke-width="3" opacity="0.7"/>
        <path d="M 60 65 Q 100 60, 140 55" fill="none" stroke="#EF4444" stroke-width="3" opacity="0.7"/>
        <path d="M 80 100 Q 100 60, 120 20" fill="none" stroke="#10B981" stroke-width="2.5" opacity="0.7"/>
    </svg>''',

    # Network Graph
    "ft_flw_4": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="60" y1="40" x2="100" y2="60" stroke="var(--border-strong)" stroke-width="1.5"/>
        <line x1="140" y1="40" x2="100" y2="60" stroke="var(--border-strong)" stroke-width="1.5"/>
        <line x1="70" y1="90" x2="100" y2="60" stroke="var(--border-strong)" stroke-width="1.5"/>
        <line x1="130" y1="90" x2="100" y2="60" stroke="var(--border-strong)" stroke-width="1.5"/>
        <circle cx="100" cy="60" r="10" fill="#2563EB"/>
        <circle cx="60" cy="40" r="7" fill="#3B82F6"/>
        <circle cx="140" cy="40" r="7" fill="#EF4444"/>
        <circle cx="70" cy="90" r="6" fill="#10B981"/>
        <circle cx="130" cy="90" r="8" fill="#F59E0B"/>
    </svg>'''
}

print(f"Bespoke FT SVGs created: {len(FT_SVGS)}")
