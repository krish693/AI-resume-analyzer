import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from collections import Counter


def create_ats_gauge(score: int) -> go.Figure:
    """
    Renders a sleek, modern semicircular gauge for ATS Match Score.
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "<b>ATS Match Score</b>", 'font': {'size': 20, 'color': '#0F172A'}},
        number={'suffix': "%", 'font': {'size': 44, 'color': '#0F172A', 'family': 'Arial'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
            'bar': {'color': "#3B82F6", 'thickness': 0.28},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#E2E8F0",
            'steps': [
                {'range': [0, 50], 'color': '#FEE2E2'},
                {'range': [50, 75], 'color': '#FEF3C7'},
                {'range': [75, 100], 'color': '#D1FAE5'}
            ],
            'threshold': {
                'line': {'color': "#10B981", 'width': 4},
                'thickness': 0.75,
                'value': 85
            }
        }
    ))
    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif")
    )
    return fig


def create_skill_radar(categories_dict: dict) -> go.Figure:
    """
    Renders a radar chart showing multidimensional candidate evaluation.
    """
    categories = [
        "Technical Skills",
        "Experience Match",
        "Education Alignment",
        "Soft Skills & Comm",
        "Tools & Ecosystem"
    ]
    values = [
        categories_dict.get("technical_skills", 75),
        categories_dict.get("experience", 70),
        categories_dict.get("education", 85),
        categories_dict.get("soft_skills", 80),
        categories_dict.get("tools_technologies", 72)
    ]
    # Close the radar loop
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(59, 130, 246, 0.25)',
        line=dict(color='#2563EB', width=2.5),
        marker=dict(size=6, color='#1D4ED8'),
        name="Candidate Profile"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color='#64748B'),
                gridcolor='#E2E8F0'
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color='#1E293B', family='Arial-Bold'),
                gridcolor='#E2E8F0'
            )
        ),
        showlegend=False,
        height=280,
        margin=dict(l=40, r=40, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def create_comparison_barchart(candidates_data: list[dict]) -> go.Figure:
    """
    Renders a multi-candidate comparative bar chart for recruiters.
    """
    names = [c["name"] for c in candidates_data]
    scores = [c["score"] for c in candidates_data]
    matched_counts = [len(c.get("matched_skills", [])) for c in candidates_data]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names,
        y=scores,
        name="ATS Match %",
        marker_color="#3B82F6",
        text=[f"{s}%" for s in scores],
        textposition="auto"
    ))
    fig.add_trace(go.Bar(
        x=names,
        y=matched_counts,
        name="Matched Skills Count",
        marker_color="#10B981",
        text=matched_counts,
        textposition="auto"
    ))

    fig.update_layout(
        barmode='group',
        title="<b>Candidate Comparison Breakdown</b>",
        xaxis_title="Candidate",
        yaxis_title="Score / Count",
        height=320,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def create_missing_skills_barchart(records: list[dict]) -> go.Figure:
    """
    Aggregates missing skills across all candidate records in the database.
    """
    all_missing = []
    for r in records:
        all_missing.extend(r.get("missing_skills", []))

    if not all_missing:
        # Default placeholder
        all_missing = ["Docker", "Kubernetes", "AWS", "FastAPI", "CI/CD", "Redis", "Terraform"]

    counts = Counter([s.strip().title() for s in all_missing if s.strip()])
    top_items = counts.most_common(8)

    skills = [item[0] for item in reversed(top_items)]
    freqs = [item[1] for item in reversed(top_items)]

    fig = go.Figure(go.Bar(
        x=freqs,
        y=skills,
        orientation='h',
        marker=dict(
            color=freqs,
            colorscale='Reds',
            line=dict(color='#DC2626', width=1)
        )
    ))
    fig.update_layout(
        title="<b>Top Missing Skills Across Applicant Pool</b>",
        xaxis_title="Number of Resumes Missing Skill",
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def create_score_distribution_chart(records: list[dict]) -> go.Figure:
    """
    Histogram of candidate ATS scores for Admin Dashboard.
    """
    scores = [r.get("ats_score", 0) for r in records] or [70, 75, 82, 65, 90, 88, 78, 85, 92, 60]

    fig = go.Figure(data=[go.Histogram(
        x=scores,
        xbins=dict(start=40, end=100, size=10),
        marker_color='#6366F1',
        opacity=0.85
    )])
    fig.update_layout(
        title="<b>Applicant Score Distribution</b>",
        xaxis_title="ATS Score Range (%)",
        yaxis_title="Count of Candidates",
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig
