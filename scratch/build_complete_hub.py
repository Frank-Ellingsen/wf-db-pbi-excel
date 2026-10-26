# -*- coding: utf-8 -*-
"""
Full build script for index.html - WF1 BoMiljo Finansiell Visuell Hub
Integrates 148 measures from _Measures.tmdl with FT Visual Vocabulary (73)
and 60 Ways to Visualize Time (60), plus 18 interactive BoMiljo charts
and an interactive Power BI Measures Catalogue.
"""
import json, re, sys

print("Reading existing index.html and measures...")
with open('index.html', 'r', encoding='utf-8') as f:
    orig_html = f.read()

with open('scratch/measures_enriched.json', 'r', encoding='utf-8') as f:
    MEASURES_LIST = json.load(f)

# Parse existing BOMILJO, FT_CATS, FT_DATA, TIME_DATA
lines = orig_html.split('\n')
ft_data_orig = None
time_data_orig = None
bomiljo_orig = None
ft_cats_orig = None

for l in lines:
    ls = l.strip()
    if ls.startswith('const FT_DATA = '):
        ft_data_orig = json.loads(ls[len('const FT_DATA = '):-1])
    elif ls.startswith('const TIME_DATA = '):
        time_data_orig = json.loads(ls[len('const TIME_DATA = '):-1])
    elif ls.startswith('const BOMILJO = '):
        bomiljo_orig = json.loads(ls[len('const BOMILJO = '):-1])
    elif ls.startswith('const FT_CATS = '):
        ft_cats_orig = json.loads(ls[len('const FT_CATS = '):-1])

print(f"Original items loaded: FT={len(ft_data_orig)}, TIME={len(time_data_orig)}, MEASURES={len(MEASURES_LIST)}")

# Import SVGs from build_svg_library
from build_svg_library import FT_SVGS

# Comprehensive SVG library for TIME_DATA
TIME_SVGS = {
    "01": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <line x1="35" y1="75" x2="65" y2="40" stroke="#2563EB" stroke-width="2"/>
        <line x1="65" y1="40" x2="95" y2="60" stroke="#2563EB" stroke-width="2"/>
        <line x1="95" y1="60" x2="125" y2="25" stroke="#2563EB" stroke-width="2"/>
        <line x1="125" y1="25" x2="155" y2="50" stroke="#2563EB" stroke-width="2"/>
        <circle cx="35" cy="75" r="4" fill="#2563EB"/><circle cx="65" cy="40" r="4" fill="#2563EB"/>
        <circle cx="95" cy="60" r="4" fill="#2563EB"/><circle cx="125" cy="25" r="4" fill="#2563EB"/><circle cx="155" cy="50" r="4" fill="#2563EB"/>
    </svg>''',
    "02": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <path d="M 30 75 Q 60 20, 95 60 T 165 25" fill="none" stroke="#2563EB" stroke-width="2.5"/>
    </svg>''',
    "03": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <polyline points="30,80 60,45 90,65 120,30 150,55 175,25" fill="none" stroke="#2563EB" stroke-width="2"/>
        <rect x="27" y="77" width="6" height="6" fill="#2563EB"/><rect x="57" y="42" width="6" height="6" fill="#2563EB"/>
        <rect x="87" y="62" width="6" height="6" fill="#2563EB"/><rect x="117" y="27" width="6" height="6" fill="#2563EB"/>
        <rect x="147" y="52" width="6" height="6" fill="#2563EB"/><rect x="172" y="22" width="6" height="6" fill="#2563EB"/>
    </svg>''',
    "04": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <polyline points="30,80 60,45 90,65 120,30 150,55 175,25" fill="none" stroke="#2563EB" stroke-width="2"/>
        <circle cx="30" cy="80" r="4" fill="var(--card-bg)" stroke="#2563EB" stroke-width="2"/>
        <circle cx="60" cy="45" r="4" fill="var(--card-bg)" stroke="#2563EB" stroke-width="2"/>
        <circle cx="90" cy="65" r="4" fill="var(--card-bg)" stroke="#2563EB" stroke-width="2"/>
        <circle cx="120" cy="30" r="4" fill="var(--card-bg)" stroke="#2563EB" stroke-width="2"/>
        <circle cx="150" cy="55" r="4" fill="var(--card-bg)" stroke="#2563EB" stroke-width="2"/>
        <circle cx="175" cy="25" r="4" fill="var(--card-bg)" stroke="#2563EB" stroke-width="2"/>
    </svg>''',
    "05": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <polyline points="30,85 60,50 90,70 120,35 150,60 175,30" fill="none" stroke="#64748B" stroke-width="2.5" stroke-dasharray="5 4"/>
    </svg>''',
    "06": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <polyline points="30,85 60,50 90,70 120,35 150,60 175,30" fill="none" stroke="#F59E0B" stroke-width="3" stroke-dasharray="2 3"/>
    </svg>''',
    "07": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <path d="M 30 80 H 60 V 50 H 90 V 70 H 120 V 35 H 150 V 60 H 175" fill="none" stroke="#2563EB" stroke-width="2.5"/>
    </svg>''',
    "08": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <polyline points="30,80 60,50 90,65 120,35 150,60 175,30" fill="none" stroke="#2563EB" stroke-width="2"/>
        <polyline points="30,70 60,85 90,75 120,80 150,70 175,65" fill="none" stroke="#F59E0B" stroke-width="2"/>
        <polyline points="30,90 60,80 90,85 120,60 150,45 175,35" fill="none" stroke="#EF4444" stroke-width="2"/>
    </svg>''',
    "09": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <polyline points="30,80 60,45 90,65 120,30 150,55 175,25" fill="none" stroke="#2563EB" stroke-width="2.5"/>
        <polyline points="30,55 60,55 90,55 120,55 150,55 175,55" fill="none" stroke="#64748B" stroke-width="2" stroke-dasharray="4 3"/>
    </svg>''',
    "10": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <polyline points="30,80 60,50 90,65 120,35 150,60 175,30" fill="none" stroke="#2563EB" stroke-width="2"/>
        <circle cx="175" cy="30" r="4" fill="#2563EB"/>
        <text x="175" y="22" font-size="9" font-weight="700" text-anchor="end" fill="#2563EB">12,6M</text>
    </svg>''',
    "11": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <polyline points="30,85 55,40 80,75 105,30 130,65 155,25 175,50" fill="none" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="2 2"/>
        <path d="M 30 75 Q 80 55, 105 45 T 175 35" fill="none" stroke="#2563EB" stroke-width="3"/>
    </svg>''',
    "12": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <polygon points="30,100 30,75 60,45 90,60 120,30 150,55 175,25 175,100" fill="#2563EB" fill-opacity="0.2"/>
        <polyline points="30,75 60,45 90,60 120,30 150,55 175,25" fill="none" stroke="#2563EB" stroke-width="2"/>
    </svg>''',
    "13": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <polygon points="30,100 30,60 60,60 90,60 120,60 150,60 175,60 175,100" fill="#64748B" fill-opacity="0.15"/>
        <polyline points="30,80 60,45 90,65 120,30 150,55 175,25" fill="none" stroke="#2563EB" stroke-width="2.5"/>
    </svg>''',
    "14": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <polygon points="30,100 30,70 60,45 90,60 120,30 150,55 175,25 175,100" fill="#2563EB" fill-opacity="0.15"/>
        <line x1="30" y1="50" x2="175" y2="50" stroke="#F59E0B" stroke-width="2" stroke-dasharray="4 3"/>
    </svg>''',
    "15": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <polygon points="30,100 30,70 60,45 90,60 120,30 150,55 175,25 175,100" fill="#2563EB" fill-opacity="0.15"/>
        <line x1="30" y1="40" x2="175" y2="40" stroke="#EF4444" stroke-width="2" stroke-dasharray="2 3"/>
    </svg>''',
    "16": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <polygon points="30,100 30,65 65,45 105,50 145,35 175,30 175,100" fill="#2563EB" fill-opacity="0.4"/>
        <polygon points="30,100 30,80 65,70 105,75 145,65 175,60 175,100" fill="#3B82F6" fill-opacity="0.6"/>
        <polygon points="30,100 30,90 65,85 105,90 145,80 175,75 175,100" fill="#1D4ED8"/>
    </svg>''',
    "17": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <rect x="30" y="20" width="145" height="80" fill="#2563EB" fill-opacity="0.3"/>
        <path d="M 30 70 Q 100 50, 175 60 L 175 100 L 30 100 Z" fill="#2563EB"/>
        <text x="100" y="55" font-size="9" font-weight="700" fill="var(--text)" text-anchor="middle">100% Normalized</text>
    </svg>''',
    "18": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <rect x="35" y="60" width="10" height="40" fill="#94A3B8" opacity="0.5"/>
        <rect x="55" y="35" width="10" height="65" fill="#94A3B8" opacity="0.5"/>
        <rect x="75" y="50" width="10" height="50" fill="#94A3B8" opacity="0.5"/>
        <rect x="95" y="25" width="10" height="75" fill="#94A3B8" opacity="0.5"/>
        <rect x="115" y="45" width="10" height="55" fill="#94A3B8" opacity="0.5"/>
        <rect x="135" y="20" width="10" height="80" fill="#94A3B8" opacity="0.5"/>
        <rect x="155" y="30" width="10" height="70" fill="#94A3B8" opacity="0.5"/>
        <path d="M 40 60 Q 90 40, 160 30" fill="none" stroke="#2563EB" stroke-width="3"/>
    </svg>''',
    "19": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="60" x2="180" y2="60" stroke="var(--border-strong)" stroke-width="1.5"/>
        <rect x="35" y="40" width="14" height="20" fill="#10B981" rx="1"/>
        <rect x="55" y="60" width="14" height="30" fill="#EF4444" rx="1"/>
        <rect x="75" y="45" width="14" height="15" fill="#10B981" rx="1"/>
        <rect x="95" y="60" width="14" height="25" fill="#EF4444" rx="1"/>
        <rect x="115" y="30" width="14" height="30" fill="#10B981" rx="1"/>
        <rect x="135" y="60" width="14" height="35" fill="#EF4444" rx="1"/>
    </svg>''',
    "20": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="60" x2="180" y2="60" stroke="var(--border)" stroke-width="1.5"/>
        <polyline points="35,45 65,75 95,50 125,80 155,35" fill="none" stroke="#2563EB" stroke-width="2"/>
        <circle cx="35" cy="45" r="3.5" fill="#10B981"/>
        <circle cx="65" cy="75" r="3.5" fill="#EF4444"/>
        <circle cx="95" cy="50" r="3.5" fill="#10B981"/>
        <circle cx="125" cy="80" r="3.5" fill="#EF4444"/>
        <circle cx="155" cy="35" r="3.5" fill="#10B981"/>
    </svg>''',
    "21": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="75" x2="180" y2="75" stroke="var(--border-strong)" stroke-width="1.5"/>
        <polyline points="35,75 65,55 95,45 125,35 155,25" fill="none" stroke="#EF4444" stroke-width="2.5"/>
        <text x="35" y="90" font-size="8" fill="var(--text-dim)">P01 Baseline</text>
    </svg>''',
    "22": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="80" x2="180" y2="80" stroke="var(--border)" stroke-width="1.5"/>
        <path d="M 35 80 Q 95 65, 155 30" fill="none" stroke="#2563EB" stroke-width="2.5"/>
        <circle cx="155" cy="30" r="4" fill="#EF4444"/>
        <text x="155" y="22" font-size="9" font-weight="700" fill="#EF4444">+28%</text>
    </svg>''',
    "23": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <path d="M 30 100 Q 100 90, 130 50 T 175 20" fill="none" stroke="#2563EB" stroke-width="3"/>
        <line x1="30" y1="100" x2="175" y2="35" stroke="#64748B" stroke-width="1.5" stroke-dasharray="3 3"/>
        <circle cx="175" cy="20" r="4" fill="#EF4444"/>
        <text x="175" y="14" font-size="8" font-weight="700" text-anchor="end" fill="#EF4444">12,6M Actual</text>
    </svg>''',
    "24": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <polygon points="30,100 30,100 80,90 120,60 175,25 175,100" fill="#2563EB" fill-opacity="0.25"/>
        <path d="M 30 100 Q 100 90, 120 60 T 175 25" fill="none" stroke="#2563EB" stroke-width="2.5"/>
    </svg>''',
    "25": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <line x1="60" y1="20" x2="60" y2="100" stroke="#F59E0B" stroke-width="1.5" stroke-dasharray="3 2"/>
        <path d="M 60 100 Q 110 85, 175 30" fill="none" stroke="#2563EB" stroke-width="2.5"/>
        <text x="60" y="16" font-size="8" font-weight="700" fill="#F59E0B">Vikarbyrå Start</text>
    </svg>''',
    "26": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <rect x="28" y="45" width="10" height="55" fill="#2563EB" rx="1"/>
        <rect x="42" y="30" width="10" height="70" fill="#2563EB" rx="1"/>
        <rect x="56" y="50" width="10" height="50" fill="#2563EB" rx="1"/>
        <rect x="70" y="25" width="10" height="75" fill="#2563EB" rx="1"/>
        <rect x="84" y="40" width="10" height="60" fill="#2563EB" rx="1"/>
        <rect x="98" y="65" width="10" height="35" fill="#2563EB" rx="1"/>
        <rect x="112" y="20" width="10" height="80" fill="#EF4444" rx="1"/>
        <rect x="126" y="28" width="10" height="72" fill="#EF4444" rx="1"/>
        <rect x="140" y="45" width="10" height="55" fill="#94A3B8" opacity="0.4" rx="1"/>
        <rect x="154" y="50" width="10" height="50" fill="#94A3B8" opacity="0.4" rx="1"/>
    </svg>''',
    "27": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <rect x="40" y="65" width="16" height="35" fill="#2563EB"/><rect x="40" y="45" width="16" height="20" fill="#3B82F6"/><rect x="40" y="35" width="16" height="10" fill="#EF4444"/>
        <rect x="70" y="55" width="16" height="45" fill="#2563EB"/><rect x="70" y="35" width="16" height="20" fill="#3B82F6"/><rect x="70" y="20" width="16" height="15" fill="#EF4444"/>
        <rect x="100" y="50" width="16" height="50" fill="#2563EB"/><rect x="100" y="30" width="16" height="20" fill="#3B82F6"/><rect x="100" y="15" width="16" height="15" fill="#EF4444"/>
        <rect x="130" y="60" width="16" height="40" fill="#2563EB"/><rect x="130" y="45" width="16" height="15" fill="#3B82F6"/><rect x="130" y="25" width="16" height="20" fill="#EF4444"/>
    </svg>''',
    "28": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <rect x="40" y="25" width="16" height="75" fill="#2563EB"/>
        <rect x="40" y="25" width="16" height="25" fill="#EF4444"/>
        <rect x="70" y="25" width="16" height="75" fill="#2563EB"/>
        <rect x="70" y="25" width="16" height="35" fill="#EF4444"/>
        <rect x="100" y="25" width="16" height="75" fill="#2563EB"/>
        <rect x="100" y="25" width="16" height="30" fill="#EF4444"/>
        <rect x="130" y="25" width="16" height="75" fill="#2563EB"/>
        <rect x="130" y="25" width="16" height="40" fill="#EF4444"/>
    </svg>''',
    "29": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <rect x="35" y="45" width="10" height="55" fill="#64748B"/><rect x="46" y="35" width="10" height="65" fill="#2563EB"/>
        <rect x="75" y="45" width="10" height="55" fill="#64748B"/><rect x="86" y="25" width="10" height="75" fill="#EF4444"/>
        <rect x="115" y="45" width="10" height="55" fill="#64748B"/><rect x="126" y="55" width="10" height="45" fill="#10B981"/>
    </svg>''',
    "30": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <rect x="30" y="40" width="8" height="60" fill="#2563EB"/><rect x="40" y="30" width="8" height="70" fill="#2563EB"/><rect x="50" y="50" width="8" height="50" fill="#2563EB"/><rect x="60" y="25" width="8" height="75" fill="#2563EB"/>
        <line x1="28" y1="105" x2="70" y2="105" stroke="var(--border-strong)" stroke-width="2"/>
        <text x="49" y="115" font-size="8" text-anchor="middle" fill="var(--text-dim)">Tertial 1</text>
        <rect x="90" y="40" width="8" height="60" fill="#EF4444"/><rect x="100" y="65" width="8" height="35" fill="#EF4444"/><rect x="110" y="20" width="8" height="80" fill="#EF4444"/><rect x="120" y="28" width="8" height="72" fill="#EF4444"/>
        <line x1="88" y1="105" x2="130" y2="105" stroke="var(--border-strong)" stroke-width="2"/>
        <text x="109" y="115" font-size="8" text-anchor="middle" fill="var(--text-dim)">Tertial 2</text>
    </svg>''',
    "31": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <line x1="40" y1="100" x2="40" y2="45" stroke="#2563EB" stroke-width="1.5"/><circle cx="40" cy="45" r="4" fill="#2563EB"/>
        <line x1="70" y1="100" x2="70" y2="30" stroke="#2563EB" stroke-width="1.5"/><circle cx="70" cy="30" r="4" fill="#2563EB"/>
        <line x1="100" y1="100" x2="100" y2="60" stroke="#2563EB" stroke-width="1.5"/><circle cx="100" cy="60" r="4" fill="#2563EB"/>
        <line x1="130" y1="100" x2="130" y2="20" stroke="#EF4444" stroke-width="1.5"/><circle cx="130" cy="20" r="4.5" fill="#EF4444"/>
        <line x1="160" y1="100" x2="160" y2="25" stroke="#EF4444" stroke-width="1.5"/><circle cx="160" cy="25" r="4.5" fill="#EF4444"/>
    </svg>''',
    "32": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <rect x="35" y="40" width="22" height="60" fill="#94A3B8" opacity="0.3"/>
        <rect x="40" y="50" width="12" height="50" fill="#2563EB"/>
        <rect x="80" y="40" width="22" height="60" fill="#94A3B8" opacity="0.3"/>
        <rect x="85" y="25" width="12" height="75" fill="#EF4444"/>
        <rect x="125" y="40" width="22" height="60" fill="#94A3B8" opacity="0.3"/>
        <rect x="130" y="30" width="12" height="70" fill="#EF4444"/>
    </svg>''',
    "33": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1.5"/>
        <rect x="35" y="55" width="12" height="45" fill="#2563EB"/>
        <rect x="65" y="35" width="12" height="65" fill="#EF4444"/>
        <rect x="95" y="60" width="12" height="40" fill="#2563EB"/>
        <rect x="125" y="30" width="12" height="70" fill="#EF4444"/>
        <rect x="155" y="32" width="12" height="68" fill="#EF4444"/>
        <line x1="20" y1="50" x2="180" y2="50" stroke="#F59E0B" stroke-width="2" stroke-dasharray="4 2"/>
        <text x="180" y="45" font-size="8" font-weight="700" text-anchor="end" fill="#F59E0B">Budsjettmål: 1,44M</text>
    </svg>''',
    "34": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="100" x2="175" y2="100" stroke="var(--border)" stroke-width="1"/>
        <line x1="25" y1="20" x2="25" y2="100" stroke="#2563EB" stroke-width="1.5"/>
        <line x1="175" y1="20" x2="175" y2="100" stroke="#F59E0B" stroke-width="1.5"/>
        <rect x="40" y="50" width="14" height="50" fill="#2563EB" opacity="0.4"/>
        <rect x="75" y="30" width="14" height="70" fill="#2563EB" opacity="0.4"/>
        <rect x="110" y="60" width="14" height="40" fill="#2563EB" opacity="0.4"/>
        <rect x="145" y="25" width="14" height="75" fill="#2563EB" opacity="0.4"/>
        <path d="M 47 65 L 82 45 L 117 70 L 152 35" fill="none" stroke="#F59E0B" stroke-width="2.5"/>
    </svg>''',
    "35": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="100" x2="175" y2="100" stroke="var(--border)" stroke-width="1"/>
        <rect x="40" y="60" width="14" height="40" fill="#94A3B8" opacity="0.5"/>
        <rect x="80" y="40" width="14" height="60" fill="#94A3B8" opacity="0.5"/>
        <rect x="120" y="30" width="14" height="70" fill="#94A3B8" opacity="0.5"/>
        <path d="M 47 80 L 87 55 L 127 25" fill="none" stroke="#2563EB" stroke-width="2.5"/>
    </svg>''',
    "36": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="60" x2="180" y2="60" stroke="#64748B" stroke-width="1.5" stroke-dasharray="3 2"/>
        <rect x="35" y="40" width="14" height="20" fill="#10B981"/>
        <rect x="65" y="60" width="14" height="30" fill="#EF4444"/>
        <rect x="95" y="35" width="14" height="25" fill="#10B981"/>
        <rect x="125" y="60" width="14" height="35" fill="#EF4444"/>
        <rect x="155" y="60" width="14" height="25" fill="#EF4444"/>
    </svg>''',
    "37": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="65" x2="95" y2="65" stroke="#64748B" stroke-width="1"/>
        <line x1="105" y1="55" x2="175" y2="55" stroke="#64748B" stroke-width="1"/>
        <rect x="35" y="50" width="10" height="15" fill="#10B981"/><rect x="55" y="65" width="10" height="20" fill="#EF4444"/><rect x="75" y="45" width="10" height="20" fill="#10B981"/>
        <rect x="115" y="55" width="10" height="35" fill="#EF4444"/><rect x="135" y="55" width="10" height="30" fill="#EF4444"/><rect x="155" y="40" width="10" height="15" fill="#10B981"/>
    </svg>''',
    "38": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <!-- Cycle plot -->
        <line x1="25" y1="95" x2="65" y2="95" stroke="var(--border)" stroke-width="1"/>
        <line x1="75" y1="95" x2="115" y2="95" stroke="var(--border)" stroke-width="1"/>
        <line x1="125" y1="95" x2="165" y2="95" stroke="var(--border)" stroke-width="1"/>
        <polyline points="30,85 45,70 60,50" fill="none" stroke="#2563EB" stroke-width="2"/>
        <polyline points="80,90 95,80 110,35" fill="none" stroke="#EF4444" stroke-width="2"/>
        <polyline points="130,80 145,55 160,25" fill="none" stroke="#EF4444" stroke-width="2"/>
        <text x="45" y="108" font-size="8" text-anchor="middle" fill="var(--text-dim)">Jan-Mars</text>
        <text x="95" y="108" font-size="8" text-anchor="middle" fill="var(--text-dim)">Juli (Ferie)</text>
        <text x="145" y="108" font-size="8" text-anchor="middle" fill="var(--text-dim)">August</text>
    </svg>''',
    "39": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <g transform="translate(45, 18)">
            <!-- 5x4 calendar tiles -->
            <rect x="0" y="0" width="18" height="18" fill="#DBEAFE"/><rect x="22" y="0" width="18" height="18" fill="#DBEAFE"/><rect x="44" y="0" width="18" height="18" fill="#3B82F6"/><rect x="66" y="0" width="18" height="18" fill="#1D4ED8"/><rect x="88" y="0" width="18" height="18" fill="#EF4444"/>
            <rect x="0" y="22" width="18" height="18" fill="#DBEAFE"/><rect x="22" y="22" width="18" height="18" fill="#93C5FD"/><rect x="44" y="22" width="18" height="18" fill="#3B82F6"/><rect x="66" y="22" width="18" height="18" fill="#EF4444"/><rect x="88" y="22" width="18" height="18" fill="#DC2626"/>
            <rect x="0" y="44" width="18" height="18" fill="#93C5FD"/><rect x="22" y="44" width="18" height="18" fill="#3B82F6"/><rect x="44" y="44" width="18" height="18" fill="#1D4ED8"/><rect x="66" y="44" width="18" height="18" fill="#EF4444"/><rect x="88" y="44" width="18" height="18" fill="#EF4444"/>
            <rect x="0" y="66" width="18" height="18" fill="#DBEAFE"/><rect x="22" y="66" width="18" height="18" fill="#DBEAFE"/><rect x="44" y="66" width="18" height="18" fill="#93C5FD"/><rect x="66" y="66" width="18" height="18" fill="#3B82F6"/><rect x="88" y="66" width="18" height="18" fill="#1E40AF"/>
        </g>
    </svg>''',
    "40": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="50" y1="20" x2="50" y2="100" stroke="var(--border-strong)" stroke-width="1.5"/>
        <line x1="150" y1="20" x2="150" y2="100" stroke="var(--border-strong)" stroke-width="1.5"/>
        <line x1="50" y1="35" x2="150" y2="70" stroke="#2563EB" stroke-width="2.5"/><circle cx="50" cy="35" r="4" fill="#2563EB"/><circle cx="150" cy="70" r="4" fill="#2563EB"/>
        <line x1="50" y1="85" x2="150" y2="30" stroke="#EF4444" stroke-width="2.5"/><circle cx="50" cy="85" r="4" fill="#EF4444"/><circle cx="150" cy="30" r="4" fill="#EF4444"/>
    </svg>''',
    "41": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="30" y1="20" x2="30" y2="100" stroke="var(--border)" stroke-width="1"/>
        <line x1="80" y1="20" x2="80" y2="100" stroke="var(--border)" stroke-width="1"/>
        <line x1="130" y1="20" x2="130" y2="100" stroke="var(--border)" stroke-width="1"/>
        <line x1="170" y1="20" x2="170" y2="100" stroke="var(--border)" stroke-width="1"/>
        <polyline points="30,40 80,50 130,70 170,80" fill="none" stroke="#2563EB" stroke-width="2"/>
        <polyline points="30,85 80,80 130,45 170,25" fill="none" stroke="#EF4444" stroke-width="2.5"/>
    </svg>''',
    "42": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="100" y1="15" x2="100" y2="105" stroke="var(--border-strong)" stroke-width="1.5"/>
        <rect x="50" y="25" width="50" height="12" fill="#2563EB"/><rect x="100" y="25" width="20" height="12" fill="#EF4444"/>
        <rect x="40" y="45" width="60" height="12" fill="#2563EB"/><rect x="100" y="45" width="45" height="12" fill="#EF4444"/>
        <rect x="30" y="65" width="70" height="12" fill="#2563EB"/><rect x="100" y="65" width="65" height="12" fill="#EF4444"/>
        <rect x="55" y="85" width="45" height="12" fill="#2563EB"/><rect x="100" y="85" width="30" height="12" fill="#EF4444"/>
    </svg>''',
    "43": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="95" y1="20" x2="95" y2="100" stroke="var(--border-strong)" stroke-width="1"/>
        <line x1="105" y1="20" x2="105" y2="100" stroke="var(--border-strong)" stroke-width="1"/>
        <rect x="45" y="30" width="50" height="12" fill="#2563EB"/><rect x="105" y="30" width="60" height="12" fill="#EF4444"/>
        <rect x="30" y="55" width="65" height="12" fill="#2563EB"/><rect x="105" y="55" width="40" height="12" fill="#EF4444"/>
        <rect x="55" y="80" width="40" height="12" fill="#2563EB"/><rect x="105" y="80" width="70" height="12" fill="#EF4444"/>
    </svg>''',
    "44": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1"/>
        <circle cx="40" cy="55" r="4" fill="#2563EB"/><circle cx="70" cy="35" r="4" fill="#2563EB"/>
        <circle cx="100" cy="65" r="4" fill="#2563EB"/><circle cx="130" cy="20" r="5" fill="#EF4444"/>
        <circle cx="160" cy="28" r="5" fill="#EF4444"/>
    </svg>''',
    "45": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="60" x2="180" y2="60" stroke="var(--border)" stroke-width="1"/>
        <line x1="35" y1="40" x2="35" y2="80" stroke="#2563EB" stroke-width="2"/>
        <line x1="50" y1="45" x2="50" y2="75" stroke="#2563EB" stroke-width="2"/>
        <line x1="75" y1="35" x2="75" y2="85" stroke="#2563EB" stroke-width="2"/>
        <line x1="120" y1="40" x2="120" y2="80" stroke="#EF4444" stroke-width="2"/>
        <line x1="135" y1="30" x2="135" y2="90" stroke="#EF4444" stroke-width="3"/>
        <line x1="150" y1="30" x2="150" y2="90" stroke="#EF4444" stroke-width="3"/>
    </svg>''',
    "46": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="30" x2="175" y2="30" stroke="var(--border-subtle)" stroke-width="1"/>
        <path d="M 30 30 L 60 20 L 90 28 L 120 18 L 150 22 L 170 15" fill="none" stroke="#2563EB" stroke-width="1.5"/>
        <line x1="25" y1="60" x2="175" y2="60" stroke="var(--border-subtle)" stroke-width="1"/>
        <path d="M 30 65 L 60 55 L 90 62 L 120 45 L 150 70 L 170 85" fill="none" stroke="#EF4444" stroke-width="1.5"/>
        <line x1="25" y1="90" x2="175" y2="90" stroke="var(--border-subtle)" stroke-width="1"/>
        <path d="M 30 92 L 60 90 L 90 91 L 120 90 L 150 75 L 170 65" fill="none" stroke="#10B981" stroke-width="1.5"/>
    </svg>''',
    "47": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <g fill="#2563EB">
            <rect x="30" y="45" width="8" height="25"/><rect x="42" y="35" width="8" height="35"/><rect x="54" y="50" width="8" height="20"/>
            <rect x="66" y="25" width="8" height="45"/><rect x="78" y="40" width="8" height="30"/><rect x="90" y="55" width="8" height="15"/>
        </g>
        <g fill="#EF4444">
            <rect x="102" y="20" width="8" height="50"/><rect x="114" y="28" width="8" height="42"/><rect x="126" y="15" width="8" height="55"/>
            <rect x="138" y="30" width="8" height="40"/><rect x="150" y="25" width="8" height="45"/>
        </g>
    </svg>''',
    "48": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <polygon points="30,80 30,55 60,35 90,48 120,25 150,45 175,20 175,80" fill="#2563EB" fill-opacity="0.3"/>
        <polyline points="30,55 60,35 90,48 120,25 150,45 175,20" fill="none" stroke="#2563EB" stroke-width="1.5"/>
    </svg>''',
    "49": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="30" y1="35" x2="170" y2="35" stroke="var(--border)" stroke-width="1"/>
        <line x1="50" y1="35" x2="130" y2="35" stroke="var(--border-strong)" stroke-width="2"/>
        <circle cx="50" cy="35" r="5" fill="#64748B"/><circle cx="130" cy="35" r="5" fill="#EF4444"/>
        <line x1="30" y1="65" x2="170" y2="65" stroke="var(--border)" stroke-width="1"/>
        <line x1="60" y1="65" x2="95" y2="65" stroke="var(--border-strong)" stroke-width="2"/>
        <circle cx="60" cy="65" r="5" fill="#64748B"/><circle cx="95" cy="65" r="5" fill="#10B981"/>
        <line x1="30" y1="95" x2="170" y2="95" stroke="var(--border)" stroke-width="1"/>
        <line x1="45" y1="95" x2="155" y2="95" stroke="var(--border-strong)" stroke-width="2"/>
        <circle cx="45" cy="95" r="5" fill="#64748B"/><circle cx="155" cy="95" r="5" fill="#EF4444"/>
    </svg>''',
    "50": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <rect x="40" y="25" width="80" height="16" rx="8" fill="#2563EB" fill-opacity="0.25"/>
        <circle cx="48" cy="33" r="4" fill="#2563EB"/><circle cx="112" cy="33" r="4" fill="#2563EB"/>
        <rect x="60" y="55" width="95" height="16" rx="8" fill="#EF4444" fill-opacity="0.25"/>
        <circle cx="68" cy="63" r="4" fill="#EF4444"/><circle cx="147" cy="63" r="4" fill="#EF4444"/>
        <rect x="50" y="85" width="60" height="16" rx="8" fill="#10B981" fill-opacity="0.25"/>
        <circle cx="58" cy="93" r="4" fill="#10B981"/><circle cx="102" cy="93" r="4" fill="#10B981"/>
    </svg>''',
    "51": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="60" x2="180" y2="60" stroke="var(--border)" stroke-width="1.5"/>
        <circle cx="45" cy="60" r="10" fill="#2563EB" opacity="0.6"/>
        <circle cx="85" cy="60" r="18" fill="#2563EB" opacity="0.6"/>
        <circle cx="130" cy="60" r="28" fill="#EF4444" opacity="0.6"/>
        <circle cx="165" cy="60" r="22" fill="#EF4444" opacity="0.6"/>
    </svg>''',
    "52": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <path d="M 30 30 Q 70 30, 100 80 T 170 80" fill="none" stroke="#EF4444" stroke-width="2.5"/>
        <path d="M 30 80 Q 70 80, 100 30 T 170 30" fill="none" stroke="#10B981" stroke-width="2.5"/>
        <circle cx="30" cy="30" r="4" fill="#EF4444"/><circle cx="170" cy="80" r="4" fill="#EF4444"/>
        <circle cx="30" cy="80" r="4" fill="#10B981"/><circle cx="170" cy="30" r="4" fill="#10B981"/>
    </svg>''',
    "53": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="60" x2="180" y2="60" stroke="var(--border)" stroke-width="1"/>
        <path d="M 25 60 L 45 58 L 55 62 L 65 52 L 75 68 L 85 30 L 90 90 L 95 20 L 100 100 L 105 45 L 115 65 L 135 56 L 145 78 L 150 25 L 155 85 L 175 60" fill="none" stroke="#EF4444" stroke-width="1.5"/>
    </svg>''',
    "54": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="35" y1="20" x2="35" y2="100" stroke="var(--border)" stroke-width="1"/>
        <line x1="80" y1="20" x2="80" y2="100" stroke="var(--border)" stroke-width="1"/>
        <line x1="125" y1="20" x2="125" y2="100" stroke="var(--border)" stroke-width="1"/>
        <line x1="165" y1="20" x2="165" y2="100" stroke="var(--border)" stroke-width="1"/>
        <polyline points="35,40 80,60 125,50 165,85" fill="none" stroke="#2563EB" stroke-width="2"/>
        <polyline points="35,80 80,35 125,80 165,25" fill="none" stroke="#EF4444" stroke-width="2.5"/>
    </svg>''',
    "55": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <circle cx="55" cy="40" r="18" fill="none" stroke="#2563EB" stroke-width="6"/>
        <circle cx="145" cy="40" r="18" fill="none" stroke="#2563EB" stroke-width="6"/>
        <circle cx="55" cy="85" r="18" fill="none" stroke="#EF4444" stroke-width="6"/>
        <circle cx="145" cy="85" r="18" fill="none" stroke="#EF4444" stroke-width="6"/>
    </svg>''',
    "56": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="25" y1="105" x2="175" y2="105" stroke="var(--border)" stroke-width="1"/>
        <line x1="25" y1="15" x2="25" y2="105" stroke="var(--border)" stroke-width="1"/>
        <path d="M 40 80 L 65 45 L 105 35 L 135 60 L 160 30" fill="none" stroke="#2563EB" stroke-width="2"/>
        <circle cx="40" cy="80" r="4" fill="#2563EB"/><circle cx="160" cy="30" r="5" fill="#EF4444"/>
    </svg>''',
    "57": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <path d="M 40 80 L 70 50 L 110 40 L 140 65" fill="none" stroke="#2563EB" stroke-width="2"/>
        <path d="M 140 65 L 165 35" fill="none" stroke="#F59E0B" stroke-width="2.5" stroke-dasharray="3 3"/>
        <circle cx="140" cy="65" r="4" fill="#2563EB"/><circle cx="165" cy="35" r="4" fill="#F59E0B"/>
    </svg>''',
    "58": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <path d="M 40 80 L 70 50 L 110 40 L 140 65" fill="none" stroke="#2563EB" stroke-width="2"/>
        <circle cx="140" cy="65" r="6" fill="#EF4444"/>
        <circle cx="140" cy="65" r="10" fill="none" stroke="#EF4444" stroke-width="1.5" stroke-dasharray="2 2"/>
    </svg>''',
    "59": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <rect x="35" y="60" width="16" height="40" fill="#64748B"/>
        <rect x="60" y="45" width="16" height="15" fill="#EF4444"/>
        <rect x="85" y="30" width="16" height="15" fill="#EF4444"/>
        <rect x="110" y="30" width="16" height="10" fill="#10B981"/>
        <rect x="135" y="20" width="16" height="20" fill="#EF4444"/>
        <rect x="160" y="20" width="16" height="80" fill="#EF4444"/>
    </svg>''',
    "60": '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <!-- OHLC / Candlestick -->
        <g stroke="#10B981" stroke-width="1.5">
            <line x1="45" y1="30" x2="45" y2="90"/>
            <rect x="40" y="45" width="10" height="30" fill="#10B981"/>
        </g>
        <g stroke="#EF4444" stroke-width="1.5">
            <line x1="85" y1="20" x2="85" y2="95"/>
            <rect x="80" y="30" width="10" height="50" fill="#EF4444"/>
        </g>
        <g stroke="#EF4444" stroke-width="1.5">
            <line x1="125" y1="15" x2="125" y2="85"/>
            <rect x="120" y="25" width="10" height="45" fill="#EF4444"/>
        </g>
        <g stroke="#10B981" stroke-width="1.5">
            <line x1="160" y1="40" x2="160" y2="80"/>
            <rect x="155" y="50" width="10" height="20" fill="#10B981"/>
        </g>
    </svg>'''
}

# Update FT_DATA items
for item in ft_data_orig:
    fid = item['id']
    if fid in FT_SVGS:
        item['svg'] = FT_SVGS[fid]
    
    # Specific measure mapping
    if fid == 'ft_dev_1':
        item['pbi'] = "Clustered Bar med Y = dim_account[account_name], X = [ERP Avvik YTD]. Betinget farge med [ERP RAG Color]."
    elif fid == 'ft_dev_2':
        item['pbi'] = "Diverging Stacked Bar med [ERP Mindreforbruk] (venstre) og [ERP Merforbruk] (høyre) fordelt på dim_account[main_group_name]."
    elif fid == 'ft_dev_3':
        item['pbi'] = "Tornado/Spine visual med venstre akse = [ERP Regnskap] filtrert på fastlønn (101000) og høyre akse = vikarer/overtid (102000-104000)."
    elif fid == 'ft_dev_4':
        item['pbi'] = "Area visual med [ERP Regnskap] og [ERP Budsjett], med betinget rød skygge når [ERP Regnskap] > [ERP Budsjett]."
    elif fid == 'ft_cor_1':
        item['pbi'] = "Scatter chart med X = [ERP Budsjett], Y = [ERP Regnskap], Størrelse = [ERP Absolutt Avvik], Detaljer = dim_account[account_name]."
    elif fid == 'ft_cor_2':
        item['pbi'] = "Line and Clustered Column Chart med Kolonner = [ERP Regnskap] og Linje = [ERP Budsjettforbruk %]."
    elif fid == 'ft_rnk_1':
        item['pbi'] = "Ordered Bar med Y = dim_account[account_name], X = [ERP Absolutt Avvik], sortert synkende med [ERP Konto Rank Avvik]."
    elif fid == 'ft_dst_1':
        item['pbi'] = "Histogram / Binned Column med X = Avviksintervall og Y = [ERP Rader]."
    elif fid == 'ft_dst_5':
        item['pbi'] = "Box & Whisker visual med akse = dim_kostra_function[kostra_function_name], verdi = [ERP Regnskap]."
    elif fid == 'ft_dst_8':
        item['pbi'] = "Pareto Chart med Kolonner = [ERP Negativ Kostnadsdriver] og Linje = [ERP Pareto Kumulativ %] mot 80% linje [ERP Pareto 80 %]."
    elif fid == 'ft_tim_1':
        item['pbi'] = "Line Chart med X = dim_date[year_month], Linje 1 = [ERP Regnskap], Linje 2 = [ERP Budsjett]."
    elif fid == 'ft_tim_6':
        item['pbi'] = "Fan Chart / Forecasting visual med Historisk = [ERP Actual Historical] og Prognose = [ERP Forecast Trend]."
    elif fid == 'ft_mag_11':
        item['pbi'] = "Bullet Chart (xViz) med Faktisk = [ERP Regnskap YTD], Mål = [ERP Budsjett YTD], Risikobånd = 60%, 85%, 100%."
    elif fid == 'ft_ptw_5':
        item['pbi'] = "Treemap med Gruppe = dim_account[main_group_name], Detaljer = dim_account[account_name], Verdi = [ERP Regnskap YTD]."
    elif fid == 'ft_flw_2':
        item['pbi'] = "Waterfall Chart med Kategori = dim_account[main_group_name], Y = [ERP Avvik YTD], Total = [ERP Regnskap YTD]."

# Update TIME_DATA items
for item in time_data_orig:
    num = item.get('num', '')
    if num in TIME_SVGS:
        item['svg'] = TIME_SVGS[num]
        
    # Map each time method to relevant _Measures
    if num in ['01', '02', '03', '04', '05', '06', '07']:
        item['pbi'] = f"Line Chart med dim_date[year_month] på X-akse og [ERP Regnskap] som verdi. Mål: [ERP Budsjett] som referanselinje."
    elif num in ['08', '09', '10']:
        item['pbi'] = "Line Chart med [ERP Regnskap], [ERP Budsjett], og [ERP Regnskap PY] med direkte etiketter i linjeenden."
    elif num in ['11', '18']:
        item['pbi'] = "Kombinert linjediagram med månedlig [ERP Regnskap] og glidende 3-måneders snitt [ERP Regnskap Moving Avg 3M]."
    elif num in ['12', '13', '14', '15', '16', '17']:
        item['pbi'] = "Area Chart med [ERP Regnskap Running] og [ERP Budsjett Running] for å visualisere kumulativ budsjettoppbruking."
    elif num in ['19', '20']:
        item['pbi'] = "Diverging Column / Bar visual med X = dim_date[year_month] og Y = [ERP Regnskap MoM] og [ERP Regnskap MoM %]."
    elif num in ['23', '24', '25']:
        item['pbi'] = "Kumulativ S-Kurve med [ERP Regnskap Running] mot [ERP Budsjett Running] og helårsprognose [ERP EOY Run Rate]."
    elif num in ['26', '27', '28', '29', '30']:
        item['pbi'] = "Clustered Column visual med X = dim_date[year_month], Kolonner = [ERP Regnskap] og [ERP Budsjett]."
    elif num in ['31', '32', '33']:
        item['pbi'] = "Stolpediagram med [ERP Regnskap] og horisontal referanselinje for gjennomsnittlig månedlig budsjettramme."
    elif num in ['36', '37']:
        item['pbi'] = "Avviksstolper fra nullinje med [ERP Avvik] og [ERP Avvik %] per måned."
    elif num == '38':
        item['pbi'] = "Cycle Plot i Deneb/Vega-Lite som sammenligner månedstrender på tvers av regnskapsår med [ERP Regnskap YoY]."
    elif num in ['40', '41']:
        item['pbi'] = "Slope Graph med Tertial 1 og Tertial 2 snittberegnet med [ERP Regnskap] fordelt på nøkkelkonti."
    elif num in ['42', '43']:
        item['pbi'] = "Tornado/Butterfly visual med [ERP Regnskap] fordelt på faste stillinger vs variable vikarer/overtid."
    elif num in ['46', '47', '48']:
        item['pbi'] = "Power BI Tabell / Matrise med innebygde sparklines basert på månedlig [ERP Regnskap] og datapunktindikatorer."
    elif num in ['49', '50']:
        item['pbi'] = "Dumbbell Chart (Vega-Lite) med startpunkt = [ERP Budsjett] og sluttpunkt = [ERP Regnskap] per måned."
    elif num == '59':
        item['pbi'] = "Månedlig Waterfall bro med åpningsbudsjett, månedlige over-/underskridelser [ERP Avvik], og akkumulert YTD [ERP Regnskap YTD]."
    elif num == '60':
        item['pbi'] = "Candlestick / High-Low visual som viser månedlig variasjonsspenn i timer og lønnskostnader."

print("Updated FT_DATA and TIME_DATA dictionaries.")

# Save modified datasets into JSON strings
ft_json_str = json.dumps(ft_data_orig, ensure_ascii=False)
time_json_str = json.dumps(time_data_orig, ensure_ascii=False)
measures_json_str = json.dumps(MEASURES_LIST, ensure_ascii=False)

print("Preparing new index.html with 5th Tab and 18 interactive charts...")

with open('scratch/ft_data.json', 'w', encoding='utf-8') as f:
    f.write(ft_json_str)
with open('scratch/time_data.json', 'w', encoding='utf-8') as f:
    f.write(time_json_str)
with open('scratch/measures_data.json', 'w', encoding='utf-8') as f:
    f.write(measures_json_str)

print("Step 1 complete: JSON files written to scratch/.")
