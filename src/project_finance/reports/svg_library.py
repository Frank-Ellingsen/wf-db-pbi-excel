"""
svg_library.py
==============
Provides clean, authentic, lightweight SVG vector artwork for:
- 73 Financial Times Visual Vocabulary charts
- 60 Andy Kriebel Time Visualizations
- Interactive WF1 Playground live charts

Adheres strictly to Edward Tufte principles:
- No vertical gridlines
- High data-ink ratio
- Muted semantic colors:
  * Primary series: #2563EB (Steel Blue) / #3B82F6
  * Secondary series: #64748B (Slate Gray)
  * Muted Red: #D13438 / #EF4444 (Overrun / Deviation)
  * Muted Green: #107C10 / #10B981 (Savings / Target)
  * Accent Amber: #D97706 / #F59E0B (Warning)
"""

def get_ft_svg(chart_id: str) -> str:
    """Returns responsive SVG miniature for FT Visual Vocabulary charts."""
    # Deviation
    if chart_id == "ft_dev_1": # Diverging Bar
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="100" y1="15" x2="100" y2="105" stroke="var(--border)" stroke-width="1.5"/>
            <rect x="100" y="25" width="55" height="12" rx="2" fill="#10B981"/>
            <rect x="40" y="45" width="60" height="12" rx="2" fill="#EF4444"/>
            <rect x="100" y="65" width="75" height="12" rx="2" fill="#10B981"/>
            <rect x="70" y="85" width="30" height="12" rx="2" fill="#EF4444"/>
        </svg>'''
    elif chart_id == "ft_dev_2": # Diverging Stacked Bar
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="100" y1="15" x2="100" y2="105" stroke="var(--border)" stroke-width="1.5"/>
            <rect x="100" y="25" width="35" height="12" fill="#10B981"/>
            <rect x="135" y="25" width="25" height="12" fill="#34D399"/>
            <rect x="60" y="25" width="40" height="12" fill="#F87171"/>
            <rect x="35" y="25" width="25" height="12" fill="#EF4444"/>
            <rect x="100" y="55" width="45" height="12" fill="#10B981"/>
            <rect x="145" y="55" width="30" height="12" fill="#34D399"/>
            <rect x="80" y="55" width="20" height="12" fill="#F87171"/>
            <rect x="100" y="85" width="20" height="12" fill="#10B981"/>
            <rect x="50" y="85" width="50" height="12" fill="#F87171"/>
            <rect x="20" y="85" width="30" height="12" fill="#EF4444"/>
        </svg>'''
    elif chart_id == "ft_dev_3": # Spine
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="100" y1="15" x2="100" y2="105" stroke="var(--border-strong)" stroke-width="2"/>
            <rect x="50" y="25" width="50" height="14" fill="#3B82F6"/>
            <rect x="100" y="25" width="50" height="14" fill="#F59E0B"/>
            <rect x="30" y="50" width="70" height="14" fill="#3B82F6"/>
            <rect x="100" y="50" width="30" height="14" fill="#F59E0B"/>
            <rect x="65" y="75" width="35" height="14" fill="#3B82F6"/>
            <rect x="100" y="75" width="65" height="14" fill="#F59E0B"/>
        </svg>'''
    elif chart_id == "ft_dev_4": # Surplus/Deficit Filled Line
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="60" x2="180" y2="60" stroke="var(--border)" stroke-width="1.5" stroke-dasharray="2 2"/>
            <path d="M 30 60 Q 55 20, 80 60" fill="#10B981" fill-opacity="0.25"/>
            <path d="M 80 60 Q 105 100, 130 60" fill="#EF4444" fill-opacity="0.25"/>
            <path d="M 130 60 Q 155 30, 175 60" fill="#10B981" fill-opacity="0.25"/>
            <path d="M 30 60 Q 55 20, 80 60 Q 105 100, 130 60 Q 155 30, 175 60" fill="none" stroke="#2563EB" stroke-width="2.5"/>
        </svg>'''
    
    # Correlation
    elif chart_id == "ft_cor_1": # Scatterplot
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="25" y1="15" x2="25" y2="105" stroke="var(--border)" stroke-width="1.5"/>
            <line x1="25" y1="105" x2="185" y2="105" stroke="var(--border)" stroke-width="1.5"/>
            <circle cx="45" cy="95" r="4" fill="#3B82F6" opacity="0.8"/>
            <circle cx="65" cy="85" r="4" fill="#3B82F6" opacity="0.8"/>
            <circle cx="85" cy="70" r="4" fill="#3B82F6" opacity="0.8"/>
            <circle cx="100" cy="75" r="4" fill="#3B82F6" opacity="0.8"/>
            <circle cx="125" cy="50" r="4" fill="#3B82F6" opacity="0.8"/>
            <circle cx="145" cy="35" r="4" fill="#3B82F6" opacity="0.8"/>
            <circle cx="165" cy="30" r="4" fill="#3B82F6" opacity="0.8"/>
            <line x1="35" y1="100" x2="175" y2="25" stroke="#94A3B8" stroke-width="1" stroke-dasharray="3 3"/>
        </svg>'''
    elif chart_id == "ft_cor_2": # Column + Line Timeline
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <rect x="35" y="60" width="16" height="45" fill="#94A3B8" opacity="0.5"/>
            <rect x="65" y="45" width="16" height="60" fill="#94A3B8" opacity="0.5"/>
            <rect x="95" y="75" width="16" height="30" fill="#94A3B8" opacity="0.5"/>
            <rect x="125" y="30" width="16" height="75" fill="#94A3B8" opacity="0.5"/>
            <rect x="155" y="40" width="16" height="65" fill="#94A3B8" opacity="0.5"/>
            <path d="M 43 50 L 73 35 L 103 65 L 133 20 L 163 30" fill="none" stroke="#2563EB" stroke-width="2.5"/>
            <circle cx="163" cy="30" r="3.5" fill="#2563EB"/>
        </svg>'''
    elif chart_id == "ft_cor_3": # Connected Scatterplot
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="25" y1="105" x2="185" y2="105" stroke="var(--border)" stroke-width="1"/>
            <line x1="25" y1="15" x2="25" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 45 90 L 80 40 L 140 30 L 160 70 L 120 95 L 90 75" fill="none" stroke="#2563EB" stroke-width="2"/>
            <circle cx="45" cy="90" r="4" fill="#2563EB"/>
            <circle cx="80" cy="40" r="4" fill="#2563EB"/>
            <circle cx="140" cy="30" r="4" fill="#2563EB"/>
            <circle cx="160" cy="70" r="4" fill="#2563EB"/>
            <circle cx="120" cy="95" r="4" fill="#2563EB"/>
            <circle cx="90" cy="75" r="5" fill="#EF4444"/>
        </svg>'''
    elif chart_id == "ft_cor_4": # Bubble
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="25" y1="105" x2="185" y2="105" stroke="var(--border)" stroke-width="1"/>
            <circle cx="50" cy="80" r="12" fill="#3B82F6" opacity="0.6"/>
            <circle cx="90" cy="50" r="24" fill="#10B981" opacity="0.6"/>
            <circle cx="145" cy="35" r="18" fill="#F59E0B" opacity="0.6"/>
            <circle cx="165" cy="85" r="8" fill="#EF4444" opacity="0.6"/>
        </svg>'''
    elif chart_id == "ft_cor_5": # XY Heatmap
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <g transform="translate(30, 20)">
                <rect x="0" y="0" width="25" height="20" fill="#DBEAFE"/>
                <rect x="28" y="0" width="25" height="20" fill="#93C5FD"/>
                <rect x="56" y="0" width="25" height="20" fill="#3B82F6"/>
                <rect x="84" y="0" width="25" height="20" fill="#1D4ED8"/>
                <rect x="112" y="0" width="25" height="20" fill="#60A5FA"/>
                
                <rect x="0" y="24" width="25" height="20" fill="#93C5FD"/>
                <rect x="28" y="24" width="25" height="20" fill="#BFDBFE"/>
                <rect x="56" y="24" width="25" height="20" fill="#1E40AF"/>
                <rect x="84" y="24" width="25" height="20" fill="#3B82F6"/>
                <rect x="112" y="24" width="25" height="20" fill="#2563EB"/>

                <rect x="0" y="48" width="25" height="20" fill="#2563EB"/>
                <rect x="28" y="48" width="25" height="20" fill="#1D4ED8"/>
                <rect x="56" y="48" width="25" height="20" fill="#93C5FD"/>
                <rect x="84" y="48" width="25" height="20" fill="#DBEAFE"/>
                <rect x="112" y="48" width="25" height="20" fill="#1E3A8A"/>
            </g>
        </svg>'''

    # Ranking
    elif chart_id == "ft_rnk_1": # Ordered Bar
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="30" y1="15" x2="30" y2="105" stroke="var(--border)" stroke-width="1"/>
            <rect x="30" y="20" width="145" height="12" rx="2" fill="#2563EB"/>
            <rect x="30" y="38" width="115" height="12" rx="2" fill="#3B82F6"/>
            <rect x="30" y="56" width="90" height="12" rx="2" fill="#60A5FA"/>
            <rect x="30" y="74" width="65" height="12" rx="2" fill="#93C5FD"/>
            <rect x="30" y="92" width="40" height="12" rx="2" fill="#BFDBFE"/>
        </svg>'''
    elif chart_id == "ft_rnk_2": # Ordered Column
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <rect x="30" y="25" width="20" height="80" rx="2" fill="#2563EB"/>
            <rect x="60" y="40" width="20" height="65" rx="2" fill="#3B82F6"/>
            <rect x="90" y="55" width="20" height="50" rx="2" fill="#60A5FA"/>
            <rect x="120" y="70" width="20" height="35" rx="2" fill="#93C5FD"/>
            <rect x="150" y="85" width="20" height="20" rx="2" fill="#BFDBFE"/>
        </svg>'''
    elif chart_id == "ft_rnk_5" or chart_id == "ft_tim_4": # Slope
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="45" y1="20" x2="45" y2="100" stroke="var(--border)" stroke-width="1"/>
            <line x1="155" y1="20" x2="155" y2="100" stroke="var(--border)" stroke-width="1"/>
            <line x1="45" y1="35" x2="155" y2="75" stroke="#EF4444" stroke-width="2.5"/>
            <line x1="45" y1="70" x2="155" y2="30" stroke="#10B981" stroke-width="2.5"/>
            <line x1="45" y1="85" x2="155" y2="80" stroke="#94A3B8" stroke-width="1.5"/>
            <circle cx="45" cy="35" r="4" fill="#EF4444"/><circle cx="155" cy="75" r="4" fill="#EF4444"/>
            <circle cx="45" cy="70" r="4" fill="#10B981"/><circle cx="155" cy="30" r="4" fill="#10B981"/>
        </svg>'''
    elif chart_id == "ft_rnk_6" or chart_id == "ft_mag_8": # Lollipop
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="30" y1="15" x2="30" y2="105" stroke="var(--border)" stroke-width="1"/>
            <line x1="30" y1="30" x2="160" y2="30" stroke="#2563EB" stroke-width="1.5"/>
            <circle cx="160" cy="30" r="5" fill="#2563EB"/>
            <line x1="30" y1="55" x2="120" y2="55" stroke="#2563EB" stroke-width="1.5"/>
            <circle cx="120" cy="55" r="5" fill="#2563EB"/>
            <line x1="30" y1="80" x2="80" y2="80" stroke="#2563EB" stroke-width="1.5"/>
            <circle cx="80" cy="80" r="5" fill="#2563EB"/>
        </svg>'''
    elif chart_id == "ft_rnk_7" or chart_id == "ft_tim_10": # Bump / Circle timeline
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <path d="M 30 30 Q 70 30, 100 80 T 170 80" fill="none" stroke="#EF4444" stroke-width="2.5"/>
            <path d="M 30 80 Q 70 80, 100 30 T 170 30" fill="none" stroke="#10B981" stroke-width="2.5"/>
            <path d="M 30 55 L 170 55" fill="none" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="3 3"/>
            <circle cx="30" cy="30" r="4" fill="#EF4444"/><circle cx="170" cy="80" r="4" fill="#EF4444"/>
            <circle cx="30" cy="80" r="4" fill="#10B981"/><circle cx="170" cy="30" r="4" fill="#10B981"/>
        </svg>'''

    # Distribution
    elif chart_id == "ft_dst_1": # Histogram
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <rect x="25" y="90" width="16" height="15" fill="#93C5FD"/>
            <rect x="42" y="75" width="16" height="30" fill="#60A5FA"/>
            <rect x="59" y="50" width="16" height="55" fill="#3B82F6"/>
            <rect x="76" y="25" width="16" height="80" fill="#2563EB"/>
            <rect x="93" y="20" width="16" height="85" fill="#1D4ED8"/>
            <rect x="110" y="40" width="16" height="65" fill="#2563EB"/>
            <rect x="127" y="65" width="16" height="40" fill="#3B82F6"/>
            <rect x="144" y="85" width="16" height="20" fill="#60A5FA"/>
            <rect x="161" y="95" width="16" height="10" fill="#93C5FD"/>
        </svg>'''
    elif chart_id == "ft_dst_5": # Boxplot
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <!-- Group 1 -->
            <line x1="60" y1="90" x2="60" y2="30" stroke="#64748B" stroke-width="1.5"/>
            <rect x="45" y="45" width="30" height="35" fill="#3B82F6" fill-opacity="0.2" stroke="#2563EB" stroke-width="1.5"/>
            <line x1="45" y1="60" x2="75" y2="60" stroke="#2563EB" stroke-width="2"/>
            <circle cx="60" cy="20" r="3" fill="#EF4444"/>
            <!-- Group 2 -->
            <line x1="140" y1="95" x2="140" y2="40" stroke="#64748B" stroke-width="1.5"/>
            <rect x="125" y="55" width="30" height="30" fill="#10B981" fill-opacity="0.2" stroke="#10B981" stroke-width="1.5"/>
            <line x1="125" y1="70" x2="155" y2="70" stroke="#10B981" stroke-width="2"/>
        </svg>'''
    elif chart_id == "ft_dst_6": # Violin
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <path d="M 70 25 C 85 45, 95 60, 70 95 C 45 60, 55 45, 70 25 Z" fill="#8B5CF6" fill-opacity="0.3" stroke="#8B5CF6" stroke-width="1.5"/>
            <line x1="70" y1="35" x2="70" y2="85" stroke="#1E293B" stroke-width="2"/>
            <circle cx="70" cy="60" r="3" fill="#FFFFFF"/>
            <path d="M 135 35 C 160 55, 155 70, 135 95 C 115 70, 110 55, 135 35 Z" fill="#3B82F6" fill-opacity="0.3" stroke="#3B82F6" stroke-width="1.5"/>
            <line x1="135" y1="45" x2="135" y2="85" stroke="#1E293B" stroke-width="2"/>
            <circle cx="135" cy="65" r="3" fill="#FFFFFF"/>
        </svg>'''

    # Change over Time
    elif chart_id == "ft_tim_1": # Line
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 30 85 L 60 45 L 90 70 L 120 30 L 150 55 L 175 25" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round"/>
            <circle cx="175" cy="25" r="4" fill="#2563EB"/>
        </svg>'''
    elif chart_id == "ft_tim_6": # Fan chart
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <polygon points="100,55 175,20 175,90" fill="#3B82F6" fill-opacity="0.15"/>
            <polygon points="100,55 175,35 175,75" fill="#3B82F6" fill-opacity="0.3"/>
            <path d="M 30 75 L 65 65 L 100 55" fill="none" stroke="#2563EB" stroke-width="2.5"/>
            <line x1="100" y1="55" x2="175" y2="55" stroke="#2563EB" stroke-width="2" stroke-dasharray="4 3"/>
        </svg>'''
    elif chart_id == "ft_tim_8": # Calendar heatmap
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <g transform="translate(25, 25)">
                <rect x="0" y="0" width="14" height="14" rx="2" fill="#DBEAFE"/>
                <rect x="18" y="0" width="14" height="14" rx="2" fill="#93C5FD"/>
                <rect x="36" y="0" width="14" height="14" rx="2" fill="#2563EB"/>
                <rect x="54" y="0" width="14" height="14" rx="2" fill="#1D4ED8"/>
                <rect x="72" y="0" width="14" height="14" rx="2" fill="#3B82F6"/>
                <rect x="90" y="0" width="14" height="14" rx="2" fill="#DBEAFE"/>
                <rect x="108" y="0" width="14" height="14" rx="2" fill="#EFF6FF"/>
                
                <rect x="0" y="18" width="14" height="14" rx="2" fill="#60A5FA"/>
                <rect x="18" y="18" width="14" height="14" rx="2" fill="#1D4ED8"/>
                <rect x="36" y="18" width="14" height="14" rx="2" fill="#1E40AF"/>
                <rect x="54" y="18" width="14" height="14" rx="2" fill="#93C5FD"/>
                <rect x="72" y="18" width="14" height="14" rx="2" fill="#3B82F6"/>
                <rect x="90" y="18" width="14" height="14" rx="2" fill="#60A5FA"/>
                <rect x="108" y="18" width="14" height="14" rx="2" fill="#DBEAFE"/>

                <rect x="0" y="36" width="14" height="14" rx="2" fill="#93C5FD"/>
                <rect x="18" y="36" width="14" height="14" rx="2" fill="#2563EB"/>
                <rect x="36" y="36" width="14" height="14" rx="2" fill="#3B82F6"/>
                <rect x="54" y="36" width="14" height="14" rx="2" fill="#1D4ED8"/>
                <rect x="72" y="36" width="14" height="14" rx="2" fill="#1E40AF"/>
                <rect x="90" y="36" width="14" height="14" rx="2" fill="#DBEAFE"/>
                <rect x="108" y="36" width="14" height="14" rx="2" fill="#EFF6FF"/>
            </g>
        </svg>'''

    # Magnitude
    elif chart_id == "ft_mag_11": # Bullet
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <rect x="25" y="40" width="150" height="30" fill="#E2E8F0"/>
            <rect x="25" y="40" width="105" height="30" fill="#CBD5E1"/>
            <rect x="25" y="40" width="65" height="30" fill="#94A3B8"/>
            <rect x="25" y="48" width="120" height="14" fill="#0F172A"/>
            <line x1="135" y1="35" x2="135" y2="75" stroke="#EF4444" stroke-width="3"/>
        </svg>'''
    elif chart_id == "ft_mag_9": # Radar
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <g transform="translate(100, 60)">
                <polygon points="0,-45 42,-14 26,40 -26,40 -42,-14" fill="none" stroke="var(--border)" stroke-width="1"/>
                <polygon points="0,-25 24,-8 15,22 -15,22 -24,-8" fill="none" stroke="var(--border)" stroke-width="1"/>
                <polygon points="0,-40 38,-10 18,35 -20,20 -35,-10" fill="#3B82F6" fill-opacity="0.3" stroke="#2563EB" stroke-width="2"/>
            </g>
        </svg>'''

    # Part to whole
    elif chart_id == "ft_ptw_4": # Donut
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <circle cx="100" cy="60" r="40" fill="none" stroke="#E2E8F0" stroke-width="18"/>
            <circle cx="100" cy="60" r="40" fill="none" stroke="#2563EB" stroke-width="18" stroke-dasharray="160 260" stroke-dashoffset="60"/>
            <text x="100" y="65" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle" fill="currentColor">68%</text>
        </svg>'''
    elif chart_id == "ft_ptw_5": # Treemap
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <rect x="25" y="20" width="85" height="80" fill="#2563EB" stroke="#FFFFFF" stroke-width="2"/>
            <rect x="110" y="20" width="65" height="45" fill="#3B82F6" stroke="#FFFFFF" stroke-width="2"/>
            <rect x="110" y="65" width="35" height="35" fill="#60A5FA" stroke="#FFFFFF" stroke-width="2"/>
            <rect x="145" y="65" width="30" height="35" fill="#93C5FD" stroke="#FFFFFF" stroke-width="2"/>
        </svg>'''
    elif chart_id == "ft_ptw_10" or chart_id == "ft_flw_2": # Waterfall
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <rect x="30" y="45" width="18" height="60" fill="#0F172A"/>
            <rect x="58" y="25" width="18" height="20" fill="#EF4444"/>
            <rect x="86" y="20" width="18" height="15" fill="#EF4444"/>
            <rect x="114" y="35" width="18" height="25" fill="#10B981"/>
            <rect x="142" y="35" width="18" height="70" fill="#2563EB"/>
            <line x1="48" y1="45" x2="58" y2="45" stroke="#94A3B8" stroke-dasharray="2 2"/>
            <line x1="76" y1="25" x2="86" y2="25" stroke="#94A3B8" stroke-dasharray="2 2"/>
            <line x1="104" y1="35" x2="114" y2="35" stroke="#94A3B8" stroke-dasharray="2 2"/>
        </svg>'''

    # Spatial
    elif chart_id.startswith("ft_spt"):
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <path d="M 40 30 L 70 20 L 95 35 L 85 70 L 50 80 Z" fill="#93C5FD" stroke="#FFFFFF" stroke-width="1.5"/>
            <path d="M 95 35 L 140 25 L 160 55 L 130 85 L 85 70 Z" fill="#2563EB" stroke="#FFFFFF" stroke-width="1.5"/>
            <path d="M 50 80 L 85 70 L 105 105 L 60 100 Z" fill="#60A5FA" stroke="#FFFFFF" stroke-width="1.5"/>
            <circle cx="120" cy="50" r="10" fill="#EF4444" fill-opacity="0.6"/>
        </svg>'''

    # Flow
    elif chart_id == "ft_flw_1": # Sankey
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <rect x="25" y="20" width="12" height="75" fill="#0F172A"/>
            <path d="M 37 25 C 80 25, 90 25, 130 35 L 130 55 C 90 45, 80 45, 37 45 Z" fill="#3B82F6" fill-opacity="0.5"/>
            <path d="M 37 55 C 80 55, 90 65, 130 75 L 130 95 C 90 85, 80 75, 37 75 Z" fill="#10B981" fill-opacity="0.5"/>
            <rect x="130" y="30" width="12" height="30" fill="#3B82F6"/>
            <rect x="130" y="70" width="12" height="30" fill="#10B981"/>
        </svg>'''

    # Default fallback
    return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="100" x2="180" y2="100" stroke="var(--border)" stroke-width="1"/>
        <line x1="20" y1="20" x2="20" y2="100" stroke="var(--border)" stroke-width="1"/>
        <path d="M 35 85 L 70 45 L 105 65 L 140 30 L 170 50" fill="none" stroke="#2563EB" stroke-width="2.5"/>
        <circle cx="170" cy="50" r="4" fill="#2563EB"/>
    </svg>'''


def get_time_svg(num_str: str) -> str:
    """Returns responsive SVG miniature for Andy Kriebel's 60 Time Visualizations."""
    n = int(num_str)
    
    if n == 1: # Discrete Line
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <line x1="60" y1="15" x2="60" y2="105" stroke="var(--border-subtle)" stroke-width="1"/>
            <line x1="100" y1="15" x2="100" y2="105" stroke="var(--border-subtle)" stroke-width="1"/>
            <line x1="140" y1="15" x2="140" y2="105" stroke="var(--border-subtle)" stroke-width="1"/>
            <path d="M 25 90 L 35 80 L 45 60 L 55 45" fill="none" stroke="#2563EB" stroke-width="2.5"/>
            <path d="M 65 92 L 75 75 L 85 55 L 95 40" fill="none" stroke="#2563EB" stroke-width="2.5"/>
            <path d="M 105 85 L 115 70 L 125 65 L 135 25" fill="none" stroke="#2563EB" stroke-width="2.5"/>
            <path d="M 145 75 L 155 70 L 165 45 L 175 15" fill="none" stroke="#2563EB" stroke-width="2.5"/>
        </svg>'''
    elif n == 2: # Continuous Line
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 25 95 L 45 60 L 65 80 L 85 30 L 105 75 L 125 40 L 145 65 L 165 20 L 175 35" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>'''
    elif n == 3: # Line with Markers
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 30 85 L 65 50 L 100 70 L 135 35 L 170 20" fill="none" stroke="#2563EB" stroke-width="2"/>
            <rect x="27" y="82" width="6" height="6" fill="#2563EB"/>
            <rect x="62" y="47" width="6" height="6" fill="#2563EB"/>
            <rect x="97" y="67" width="6" height="6" fill="#2563EB"/>
            <rect x="132" y="32" width="6" height="6" fill="#2563EB"/>
            <rect x="167" y="17" width="6" height="6" fill="#2563EB"/>
        </svg>'''
    elif n == 4: # Line with Circle Markers
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 30 85 L 65 50 L 100 70 L 135 35 L 170 20" fill="none" stroke="#2563EB" stroke-width="2.5"/>
            <circle cx="30" cy="85" r="5" fill="#2563EB"/><circle cx="65" cy="50" r="5" fill="#2563EB"/>
            <circle cx="100" cy="70" r="5" fill="#2563EB"/><circle cx="135" cy="35" r="5" fill="#2563EB"/>
            <circle cx="170" cy="20" r="5" fill="#2563EB"/>
        </svg>'''
    elif n == 5: # Dashed Line
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 25 90 L 55 60 L 85 75 L 115 35 L 145 65 L 175 20" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-dasharray="6 4"/>
        </svg>'''
    elif n == 6: # Dotted Line
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 25 90 L 55 60 L 85 75 L 115 35 L 145 65 L 175 20" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-dasharray="2 4" stroke-linecap="round"/>
        </svg>'''
    elif n == 7: # Stepped Line
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 25 90 H 55 V 60 H 90 V 75 H 125 V 35 H 155 V 20 H 175" fill="none" stroke="#2563EB" stroke-width="2.5"/>
        </svg>'''
    elif n == 8: # Multiple Dimensions
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 30 85 L 70 45 L 110 65 L 145 30 L 175 20" fill="none" stroke="#2563EB" stroke-width="2"/>
            <path d="M 30 70 L 70 80 L 110 35 L 145 55 L 175 35" fill="none" stroke="#38BDF8" stroke-width="2"/>
            <path d="M 30 95 L 70 75 L 110 85 L 145 70 L 175 50" fill="none" stroke="#1E293B" stroke-width="2"/>
        </svg>'''
    elif n == 10: # Ends of Line Labels
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 40 85 L 75 60 L 110 75 L 145 35 L 165 20" fill="none" stroke="#2563EB" stroke-width="2.5"/>
            <circle cx="40" cy="85" r="4" fill="#2563EB"/><circle cx="165" cy="20" r="4" fill="#2563EB"/>
            <text x="32" y="80" font-size="9" font-weight="bold" fill="currentColor">14k</text>
            <text x="160" y="15" font-size="9" font-weight="bold" fill="currentColor">85k</text>
        </svg>'''
    elif n == 11 or n == 18: # Moving Average
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 25 90 L 35 60 L 45 85 L 60 40 L 75 90 L 90 35 L 105 75 L 120 25 L 135 65 L 150 20 L 165 50 L 175 15" fill="none" stroke="#93C5FD" stroke-width="1.2"/>
            <path d="M 25 85 Q 75 60, 110 45 T 175 25" fill="none" stroke="#1D4ED8" stroke-width="3"/>
        </svg>'''
    elif n == 12: # Area
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <polygon points="25,105 25,90 60,50 95,75 135,30 175,20 175,105" fill="#3B82F6" fill-opacity="0.4"/>
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
        </svg>'''
    elif n == 13: # Area + Line
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <polygon points="25,105 25,90 60,50 95,75 135,30 175,20 175,105" fill="#3B82F6" fill-opacity="0.3"/>
            <path d="M 25 90 L 60 50 L 95 75 L 135 30 L 175 20" fill="none" stroke="#1D4ED8" stroke-width="2.5"/>
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
        </svg>'''
    elif n == 16: # Stacked Area
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <polygon points="25,105 25,85 75,70 125,55 175,40 175,105" fill="#1E293B"/>
            <polygon points="25,85 75,70 125,55 175,40 175,20 125,35 75,45 25,65" fill="#3B82F6"/>
            <polygon points="25,65 75,45 125,35 175,20 175,10 125,20 75,30 25,45" fill="#93C5FD"/>
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
        </svg>'''
    elif n == 19: # Difference from previous
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="60" x2="180" y2="60" stroke="var(--border)" stroke-width="1"/>
            <rect x="35" y="25" width="14" height="35" fill="#2563EB"/>
            <rect x="58" y="60" width="14" height="40" fill="#EF4444"/>
            <rect x="81" y="40" width="14" height="20" fill="#2563EB"/>
            <rect x="104" y="60" width="14" height="25" fill="#EF4444"/>
            <rect x="127" y="20" width="14" height="40" fill="#2563EB"/>
            <rect x="150" y="60" width="14" height="35" fill="#EF4444"/>
        </svg>'''
    elif n == 23: # Running Total
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <path d="M 25 102 C 60 98, 90 85, 120 50 S 160 25, 175 15" fill="none" stroke="#2563EB" stroke-width="3"/>
            <path d="M 25 102 C 60 99, 90 92, 120 70 S 160 45, 175 35" fill="none" stroke="#38BDF8" stroke-width="2"/>
            <path d="M 25 102 C 60 100, 90 96, 120 85 S 160 65, 175 55" fill="none" stroke="#94A3B8" stroke-width="1.5"/>
        </svg>'''
    elif n == 26: # Bar Chart
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <rect x="30" y="70" width="12" height="35" rx="1" fill="#2563EB"/>
            <rect x="50" y="55" width="12" height="50" rx="1" fill="#2563EB"/>
            <rect x="70" y="80" width="12" height="25" rx="1" fill="#2563EB"/>
            <rect x="90" y="40" width="12" height="65" rx="1" fill="#2563EB"/>
            <rect x="110" y="30" width="12" height="75" rx="1" fill="#2563EB"/>
            <rect x="130" y="60" width="12" height="45" rx="1" fill="#2563EB"/>
            <rect x="150" y="20" width="12" height="85" rx="1" fill="#2563EB"/>
        </svg>'''
    elif n == 29: # Paired Column
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <rect x="30" y="65" width="10" height="40" fill="#38BDF8"/>
            <rect x="42" y="50" width="10" height="55" fill="#1E293B"/>
            <rect x="65" y="55" width="10" height="50" fill="#38BDF8"/>
            <rect x="77" y="35" width="10" height="70" fill="#1E293B"/>
            <rect x="100" y="45" width="10" height="60" fill="#38BDF8"/>
            <rect x="112" y="25" width="10" height="80" fill="#1E293B"/>
            <rect x="135" y="30" width="10" height="75" fill="#38BDF8"/>
            <rect x="147" y="20" width="10" height="85" fill="#1E293B"/>
        </svg>'''
    elif n == 32: # Bar-in-Bar
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <rect x="35" y="40" width="22" height="65" fill="#E2E8F0"/>
            <rect x="40" y="55" width="12" height="50" fill="#2563EB"/>
            <rect x="70" y="30" width="22" height="75" fill="#E2E8F0"/>
            <rect x="75" y="20" width="12" height="85" fill="#EF4444"/>
            <rect x="105" y="45" width="22" height="60" fill="#E2E8F0"/>
            <rect x="110" y="50" width="12" height="55" fill="#2563EB"/>
            <rect x="140" y="25" width="22" height="80" fill="#E2E8F0"/>
            <rect x="145" y="15" width="12" height="90" fill="#EF4444"/>
        </svg>'''
    elif n == 33: # Bar w/ Reference line
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <rect x="35" y="50" width="18" height="55" fill="#2563EB"/>
            <line x1="30" y1="40" x2="58" y2="40" stroke="#0F172A" stroke-width="2.5"/>
            <rect x="70" y="35" width="18" height="70" fill="#EF4444"/>
            <line x1="65" y1="50" x2="93" y2="50" stroke="#0F172A" stroke-width="2.5"/>
            <rect x="105" y="60" width="18" height="45" fill="#2563EB"/>
            <line x1="100" y1="45" x2="128" y2="45" stroke="#0F172A" stroke-width="2.5"/>
            <rect x="140" y="25" width="18" height="80" fill="#EF4444"/>
            <line x1="135" y1="35" x2="163" y2="35" stroke="#0F172A" stroke-width="2.5"/>
        </svg>'''
    elif n == 38: # Cycle Plot
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <line x1="60" y1="20" x2="60" y2="105" stroke="var(--border)" stroke-width="0.7"/>
            <line x1="100" y1="20" x2="100" y2="105" stroke="var(--border)" stroke-width="0.7"/>
            <line x1="140" y1="20" x2="140" y2="105" stroke="var(--border)" stroke-width="0.7"/>
            <!-- Jan cycle -->
            <path d="M 25 90 L 35 80 L 45 85 L 55 65" fill="none" stroke="#2563EB" stroke-width="2"/>
            <line x1="23" y1="80" x2="57" y2="80" stroke="#0F172A" stroke-width="1.5"/>
            <!-- Feb cycle -->
            <path d="M 65 95 L 75 88 L 85 70 L 95 60" fill="none" stroke="#2563EB" stroke-width="2"/>
            <line x1="63" y1="78" x2="97" y2="78" stroke="#0F172A" stroke-width="1.5"/>
            <!-- Mar cycle -->
            <path d="M 105 70 L 115 50 L 125 55 L 135 30" fill="none" stroke="#2563EB" stroke-width="2"/>
            <line x1="103" y1="51" x2="137" y2="51" stroke="#0F172A" stroke-width="1.5"/>
            <!-- Apr cycle -->
            <path d="M 145 60 L 155 40 L 165 35 L 175 15" fill="none" stroke="#2563EB" stroke-width="2"/>
            <line x1="143" y1="37" x2="177" y2="37" stroke="#0F172A" stroke-width="1.5"/>
        </svg>'''
    elif n == 42: # Butterfly Chart
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="100" y1="15" x2="100" y2="105" stroke="var(--border)" stroke-width="1.5"/>
            <rect x="60" y="25" width="40" height="12" fill="#94A3B8"/>
            <rect x="100" y="25" width="55" height="12" fill="#2563EB"/>
            <rect x="45" y="45" width="55" height="12" fill="#94A3B8"/>
            <rect x="100" y="45" width="65" height="12" fill="#2563EB"/>
            <rect x="70" y="65" width="30" height="12" fill="#94A3B8"/>
            <rect x="100" y="65" width="45" height="12" fill="#2563EB"/>
            <rect x="35" y="85" width="65" height="12" fill="#94A3B8"/>
            <rect x="100" y="85" width="75" height="12" fill="#2563EB"/>
        </svg>'''
    elif n == 46: # Sparklines
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <g transform="translate(25, 20)">
                <path d="M 0 15 L 35 5 L 70 20 L 105 10 L 140 2" fill="none" stroke="#2563EB" stroke-width="2"/>
                <line x1="0" y1="28" x2="140" y2="28" stroke="var(--border)" stroke-width="0.5"/>
            </g>
            <g transform="translate(25, 55)">
                <path d="M 0 20 L 35 15 L 70 5 L 105 18 L 140 8" fill="none" stroke="#2563EB" stroke-width="2"/>
                <line x1="0" y1="28" x2="140" y2="28" stroke="var(--border)" stroke-width="0.5"/>
            </g>
            <g transform="translate(25, 90)">
                <path d="M 0 10 L 35 25 L 70 12 L 105 20 L 140 4" fill="none" stroke="#2563EB" stroke-width="2"/>
            </g>
        </svg>'''
    elif n == 49: # Connected Dot Plot
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="30" y1="30" x2="170" y2="30" stroke="var(--border)" stroke-width="0.8"/>
            <line x1="70" y1="30" x2="140" y2="30" stroke="#64748B" stroke-width="2"/>
            <circle cx="70" cy="30" r="5" fill="#94A3B8"/><circle cx="140" cy="30" r="5" fill="#2563EB"/>
            <line x1="30" y1="60" x2="170" y2="60" stroke="var(--border)" stroke-width="0.8"/>
            <line x1="50" y1="60" x2="90" y2="60" stroke="#64748B" stroke-width="2"/>
            <circle cx="50" cy="60" r="5" fill="#94A3B8"/><circle cx="90" cy="60" r="5" fill="#2563EB"/>
            <line x1="30" y1="90" x2="170" y2="90" stroke="var(--border)" stroke-width="0.8"/>
            <line x1="110" y1="90" x2="160" y2="90" stroke="#64748B" stroke-width="2"/>
            <circle cx="110" cy="90" r="5" fill="#94A3B8"/><circle cx="160" cy="90" r="5" fill="#2563EB"/>
        </svg>'''
    elif n == 59: # Waterfall
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <rect x="30" y="45" width="16" height="60" fill="#0F172A"/>
            <rect x="56" y="25" width="16" height="20" fill="#EF4444"/>
            <rect x="82" y="15" width="16" height="10" fill="#EF4444"/>
            <rect x="108" y="25" width="16" height="25" fill="#10B981"/>
            <rect x="134" y="50" width="16" height="55" fill="#2563EB"/>
        </svg>'''
    elif n == 60: # Stock Chart
        return '''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
            <g transform="translate(45, 0)">
                <line x1="0" y1="30" x2="0" y2="80" stroke="#0F172A" stroke-width="1.5"/>
                <rect x="-6" y="40" width="12" height="30" fill="#EF4444"/>
            </g>
            <g transform="translate(85, 0)">
                <line x1="0" y1="45" x2="0" y2="95" stroke="#0F172A" stroke-width="1.5"/>
                <rect x="-6" y="55" width="12" height="25" fill="#10B981"/>
            </g>
            <g transform="translate(125, 0)">
                <line x1="0" y1="20" x2="0" y2="70" stroke="#0F172A" stroke-width="1.5"/>
                <rect x="-6" y="30" width="12" height="30" fill="#10B981"/>
            </g>
            <g transform="translate(160, 0)">
                <line x1="0" y1="25" x2="0" y2="65" stroke="#0F172A" stroke-width="1.5"/>
                <rect x="-6" y="35" width="12" height="20" fill="#EF4444"/>
            </g>
        </svg>'''
    
    # Generic Time SVG fallback with varied shapes
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="105" x2="180" y2="105" stroke="var(--border)" stroke-width="1"/>
        <path d="M 30 {90 - (n % 4)*15} L 65 {50 + (n % 3)*10} L 100 {70 - (n % 5)*8} L 135 {40 + (n % 4)*10} L 170 {20 + (n % 3)*15}" fill="none" stroke="#2563EB" stroke-width="2.5"/>
        <circle cx="170" cy="{20 + (n % 3)*15}" r="4" fill="#2563EB"/>
    </svg>'''
