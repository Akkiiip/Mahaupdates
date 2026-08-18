import os
import re
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime
from time import monotonic
from urllib.parse import quote, unquote, urlparse, quote_plus

from flask import Flask, render_template_string, request, redirect
from notification_validation import create_client
from notification_validation import is_valid_notification_title


app = Flask(__name__)


# ============================================================
# CONFIG
# ============================================================

UPDATES_PER_PAGE = 12
MAX_PAGE_NUMBER = 1000
VALID_UPDATE_CANDIDATE_LIMIT = 5000


# ============================================================
# MAIN TEMPLATE
# ============================================================

PAGE = """
<!doctype html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>{{ page_title }} | MahaUpdate</title>

    <link rel="icon" type="image/png" href="{{ logo_data_uri }}">

    <style>

        :root {
            --navy: #0b1f3a;
            --navy-light: #173b68;
            --saffron: #f59e0b;
            --bg: #f5f7fa;
            --card: #ffffff;
            --text: #172033;
            --muted: #667085;
            --border: #e5e7eb;
            --green: #22c55e;
        }


        * {
            box-sizing: border-box;
        }


        body {
            margin: 0;

            font-family:
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                "Noto Sans Devanagari",
                sans-serif;

            background: var(--bg);

            color: var(--text);
        }


        /* ===================================================
           HEADER
        =================================================== */

        header {
            background: var(--navy);

            color: white;

            position: sticky;

            top: 0;

            z-index: 100;
        }


        .header-container {
            width: min(1100px, calc(100% - 40px));
            margin: 0 auto;
            padding: 14px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }


        .brand {

            display: flex;

            align-items: center;

            gap: 11px;

            text-decoration: none;

            color: white;

        }


        .logo {
            width: 58px;
            height: 58px;
            flex: 0 0 58px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: visible;
        }

        .logo::before { content: none; }

        .logo img {
            display: block;
            width: 62px;
            height: 62px;
            object-fit: contain;
            filter: drop-shadow(0 3px 7px rgba(0,0,0,.28));
        }


        .brand-name {font-size:24px;font-weight:900;letter-spacing:-.8px;line-height:1}
        .brand-maha{color:#f5f1e8}
        .brand-update{
            background:linear-gradient(90deg,#f6b11a,#ff7a18,#e54b22);
            -webkit-background-clip:text;
            background-clip:text;
            color:transparent;
        }


        .brand-tagline {font-size:10px;color:#c7d1df;margin-top:2px;letter-spacing:.7px;text-transform:uppercase}


        nav {

            display: flex;

            align-items: center;

            gap: 4px;

        }


        nav a {

            color: #d8e0eb;

            text-decoration: none;

            font-size: 14px;

            font-weight: 600;

            padding: 9px 12px;

            border-radius: 8px;

        }


        nav a:hover,
        nav a.active {

            background: rgba(255,255,255,.10);

            color: white;

        }


        .mobile-menu-button {

            display: none;

            background: rgba(255,255,255,.10);

            border: none;

            color: white;

            font-size: 22px;

            width: 42px;

            height: 42px;

            border-radius: 9px;

            cursor: pointer;

        }


        /* ===================================================
           PAGE
        =================================================== */

        .container {
            width: min(1100px, calc(100% - 40px));
            margin: 0 auto;
            padding: 28px 0 42px;
        }


        .hero {

            background: var(--navy);

            border-radius: 20px;

            padding: 35px;

            color: white;

            margin-bottom: 24px;

        }


        .hero h1 {

            margin: 0 0 8px;

            font-size: 32px;

        }


        .hero p {

            margin: 0;

            color: #c7d2df;

            max-width: 650px;

            line-height: 1.6;

        }


        .section-header {

            display: flex;

            justify-content: space-between;

            align-items: center;

            margin: 25px 0 15px;

        }


        .section-header h2 {

            margin: 0;

            font-size: 23px;

            color: var(--navy);

        }


        .count {

            background: white;

            border: 1px solid var(--border);

            border-radius: 20px;

            padding: 7px 12px;

            color: var(--muted);

            font-size: 12px;

            font-weight: 700;

        }


        /* ===================================================
           SOURCE CARDS
        =================================================== */

        .source-grid {

            display: grid;

            grid-template-columns: repeat(2, 1fr);

            gap: 15px;

            margin-bottom: 30px;

        }


        .source-card {

            background: white;

            border: 1px solid var(--border);

            border-radius: 16px;

            padding: 22px;

            text-decoration: none;

            color: var(--text);

            transition: .2s;

        }


        .source-card:hover {

            transform: translateY(-2px);

            box-shadow: 0 10px 25px rgba(0,0,0,.07);

        }


        .source-card h3 {

            margin: 0 0 6px;

            color: var(--navy);

        }


        .source-card p {

            margin: 0;

            color: var(--muted);

            font-size: 14px;

        }


        /* ===================================================
           FILTER PANEL
        =================================================== */

        .filter-panel {

            background: white;

            border: 1px solid var(--border);

            border-radius: 16px;

            padding: 15px;

            margin-bottom: 22px;

        }


        .filter-row {

            display: grid;

            grid-template-columns: 2fr 1fr 1fr auto;

            gap: 10px;

        }


        input,
        select {

            height: 46px;

            border: 1px solid var(--border);

            border-radius: 9px;

            padding: 0 12px;

            font-size: 14px;

            background: white;

        }


        input:focus,
        select:focus {

            outline: none;

            border-color: var(--saffron);

            box-shadow: 0 0 0 3px rgba(245,158,11,.12);

        }


        .button {

            display: inline-flex;

            justify-content: center;

            align-items: center;

            min-height: 44px;

            padding: 0 17px;

            border: none;

            border-radius: 9px;

            background: var(--navy);

            color: white;

            text-decoration: none;

            font-size: 14px;

            font-weight: 700;

            cursor: pointer;

        }


        .button:hover {

            background: var(--navy-light);

        }


        .clear-link {

            display: inline-flex;

            align-items: center;

            margin-top: 12px;

            color: var(--muted);

            text-decoration: none;

            font-size: 13px;

        }


        /* ===================================================
           UPDATE CARDS
        =================================================== */

        .updates {

            display: grid;

            gap: 13px;

        }


        .update-card {

            background: white;

            border: 1px solid var(--border);

            border-radius: 15px;

            padding: 19px;

            transition: .2s;

        }


        .update-card:hover {

            box-shadow: 0 8px 24px rgba(0,0,0,.06);

            transform: translateY(-1px);

        }


        .update-top {

            display: flex;

            justify-content: space-between;

            gap: 15px;

            margin-bottom: 12px;

        }


        .badges {

            display: flex;

            gap: 7px;

            flex-wrap: wrap;

        }


        .badge {

            padding: 5px 9px;

            border-radius: 20px;

            font-size: 11px;

            font-weight: 750;

        }


        .badge-mpsc {

            background: #eaf1ff;

            color: #285da8;

        }


        .badge-source {
            background: #eef2f7;
            color: #42526b;
        }

        .badge-midc {
            background: #fff1dc;
            color: #a65b00;
        }


        .badge-type {

            background: #f1f3f6;

            color: #586273;

        }


        .date {

            color: var(--muted);

            font-size: 12px;

            white-space: nowrap;

        }


        .update-card h3 {

            margin: 0 0 17px;

            font-size: 16px;

            font-weight: 650;

            line-height: 1.6;

            overflow-wrap: anywhere;

        }


        .official-button {

            display: inline-flex;

            justify-content: center;

            align-items: center;

            min-height: 40px;

            padding: 8px 14px;

            background: var(--navy);

            color: white;

            text-decoration: none;

            border-radius: 8px;

            font-size: 13px;

            font-weight: 700;

        }


        .official-button:hover {

            background: var(--navy-light);

        }


        /* ===================================================
           ADS
        =================================================== */

        .ad-large {

            min-height: 230px;

            border: 1px dashed #c9ced6;

            border-radius: 16px;

            background: #ffffff;

            display: flex;

            flex-direction: column;

            justify-content: center;

            align-items: center;

            color: #8b94a3;

            margin: 5px 0;

        }


        .ad-label {

            font-size: 11px;

            text-transform: uppercase;

            letter-spacing: 1px;

            margin-bottom: 8px;

            color: #a0a7b2;

        }


        .ad-large strong {

            font-size: 15px;

            color: #737d8c;

        }


        .ad-large span {

            font-size: 12px;

            margin-top: 5px;

        }


        /* ===================================================
           PAGINATION
        =================================================== */

        .pagination {

            display: flex;

            justify-content: center;

            gap: 7px;

            margin-top: 30px;

            flex-wrap: wrap;

        }


        .pagination a,
        .pagination span {

            min-width: 40px;

            height: 40px;

            display: flex;

            justify-content: center;

            align-items: center;

            border-radius: 8px;

            border: 1px solid var(--border);

            background: white;

            text-decoration: none;

            color: var(--navy);

            font-size: 13px;

            font-weight: 700;

        }


        .pagination .current {

            background: var(--navy);

            color: white;

            border-color: var(--navy);

        }


        /* ===================================================
           EMPTY / ABOUT
        =================================================== */

        .empty,
        .about-card {

            background: white;

            border: 1px solid var(--border);

            border-radius: 16px;

            padding: 35px;

            text-align: center;

            color: var(--muted);

        }


        .about-card {

            text-align: left;

            line-height: 1.8;

        }


        .about-card h2 {

            color: var(--navy);

        }


        /* ===================================================
           FOOTER
        =================================================== */

        footer {

            background: white;

            border-top: 1px solid var(--border);

            text-align: center;

            padding: 25px 15px;

            color: var(--muted);

            font-size: 12px;

        }


        /* ===================================================
           MOBILE
        =================================================== */

        @media (max-width: 750px) {

            .header-container {

                padding: 12px 15px;

            }


            .mobile-menu-button {

                display: block;

            }


            nav {

                display: none;

                position: absolute;

                top: 68px;

                left: 0;

                right: 0;

                background: var(--navy);

                padding: 12px 15px 18px;

                flex-direction: column;

                align-items: stretch;

                border-top: 1px solid rgba(255,255,255,.08);

            }


            nav.open {

                display: flex;

            }


            nav a {

                padding: 13px;

            }


            .container {

                padding: 20px 12px 35px;

            }


            .hero {

                padding: 25px 20px;

                border-radius: 16px;

            }


            .hero h1 {

                font-size: 25px;

            }


            .source-grid {

                grid-template-columns: 1fr;

            }


            .filter-row {

                grid-template-columns: 1fr;

            }


            .update-card {

                padding: 16px;

            }


            .update-top {

                flex-direction: column;

                gap: 8px;

            }


            .official-button {

                width: 100%;

                min-height: 44px;

            }


            .ad-large {

                min-height: 250px;

            }

        }


        /* ===== MahaUpdate 2.0 redesign ===== */
.hero{position:relative;overflow:hidden;background:radial-gradient(circle at 85% 0%,rgba(247,183,25,.22),transparent 26%),linear-gradient(135deg,#0b1f3a,#173b68);border:0}
        .hero:after{content:"🏛";position:absolute;right:7%;bottom:-60px;font-size:210px;opacity:.08}
        .hero h1,.hero p{position:relative;z-index:1}
        .department-showcase{background:#fff;border:1px solid var(--border);border-radius:22px;padding:22px;margin:22px 0 30px;box-shadow:0 10px 35px rgba(11,31,58,.06)}
        .department-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}
        .department-chip{min-height:122px;padding:15px 10px;border-radius:16px;background:#f7f9fc;border:1px solid #edf1f6;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;text-align:center;transition:.2s}
        .department-chip:hover{transform:translateY(-3px);background:#eef4ff;border-color:#cbdcff;box-shadow:0 12px 24px rgba(11,31,58,.09)}
        .department-icon{font-size:26px}.department-chip strong{font-size:13px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.department-chip small{font-size:11px;color:var(--muted)}
        .more-chip{background:linear-gradient(135deg,#173b68,#0b1f3a);color:#fff}.more-chip small{color:#dbe6f4}
        .section-subtitle{margin:5px 0 0;color:var(--muted);font-size:14px}
        .updates{grid-template-columns:repeat(3,1fr);gap:16px}
        .update-card{border-radius:18px;box-shadow:0 8px 25px rgba(11,31,58,.045)}
        .update-card:hover{transform:translateY(-3px);box-shadow:0 18px 38px rgba(11,31,58,.1)}
        .badge{max-width:170px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
        
        @media(max-width:1000px){.department-grid{grid-template-columns:repeat(4,1fr)}.updates{grid-template-columns:repeat(2,1fr)}}
        @media(max-width:700px){.department-showcase{padding:14px;border-radius:16px}.department-grid{grid-template-columns:repeat(3,1fr);gap:8px}.department-chip{min-height:98px;padding:10px 5px}.department-icon{font-size:22px}.department-chip strong{font-size:11px}.department-chip small{font-size:10px}.updates{grid-template-columns:1fr}}

    
        /* ===== Advertisement system ===== */
        .ad-slot{position:relative;background:#fff;border:1px solid #e3e9f1;border-radius:16px;overflow:hidden;display:flex;align-items:center;justify-content:center;color:#8a97a8;text-align:center;box-sizing:border-box}
        .ad-slot:before{content:"ADVERTISEMENT";position:absolute;top:7px;left:0;right:0;font-size:9px;letter-spacing:1.5px;color:#a5afbc;font-weight:700}
        .ad-content{padding:18px 16px;line-height:1.45}
        .ad-leaderboard{width:100%;min-height:110px;margin:24px 0;background:linear-gradient(135deg,#f8fafc,#eef3f9)}
        .ad-inline{grid-column:1/-1!important;width:100%!important;min-height:105px;margin:4px 0;background:#f8fafc}
        .ad-sidebar{width:100%;min-height:250px;margin:24px 0;background:linear-gradient(145deg,#f8fafc,#edf2f7)}
        .floating-ad{position:fixed;left:50%;bottom:12px;transform:translateX(-50%);width:min(728px,calc(100vw - 24px));height:90px;z-index:9999;background:#fff;border:1px solid #dfe6ef;border-radius:10px;box-shadow:0 10px 35px rgba(0,0,0,.20);display:flex;align-items:center;justify-content:center;box-sizing:border-box}
        .floating-ad .ad-label{position:absolute;top:5px;left:0;right:0;text-align:center;font-size:8px;letter-spacing:1.3px;color:#9aa6b5;font-weight:700}
        .floating-ad .ad-content{padding:18px 36px 8px;font-size:13px;color:#748195;text-align:center}
        .floating-ad-close{position:absolute;right:6px;top:5px;width:24px;height:24px;border:0;border-radius:50%;background:#eef2f6;color:#536174;font-size:18px;line-height:22px;cursor:pointer}
        body{padding-bottom:118px}
        @media(max-width:700px){
            .floating-ad{bottom:8px;width:calc(100vw - 16px);height:60px;border-radius:9px}
            .floating-ad .ad-content{font-size:11px;padding:14px 30px 3px}
            .floating-ad-close{right:4px;top:3px}
            body{padding-bottom:82px}
            .ad-inline{min-height:90px}
        }

/* ===== Homepage search ===== */
body[data-page="home"] .filter-panel,
.page-home .filter-panel{
    margin:24px 0 30px;
    padding:14px;
    background:#fff;
    border:1px solid #e3e9f1;
    border-radius:16px;
    box-shadow:0 8px 24px rgba(15,35,60,.06);
}
body[data-page="home"] .filter-row input,
.page-home .filter-row input{
    min-width:280px;
    flex:1 1 360px;
}
@media(max-width:700px){
    body[data-page="home"] .filter-row,
    .page-home .filter-row{display:grid;grid-template-columns:1fr;gap:10px}
    body[data-page="home"] .filter-row input,
    .page-home .filter-row input{min-width:0;width:100%}
}


        @media(max-width:700px){
            .brand{gap:8px}
            .logo{width:48px;height:48px;flex-basis:48px}
            .logo img{width:52px;height:52px}
            .brand-name{font-size:20px}
            .brand-tagline{font-size:8px;letter-spacing:.5px}
        }


/* ===== Compact mobile layout ===== */
@media(max-width:700px){
    body{padding-bottom:76px;font-size:14px}
    header .container{min-height:64px;padding:8px 14px}
    .container{padding:14px 12px 24px}
    .hero{padding:20px 16px;margin-bottom:14px;border-radius:15px}
    .hero h1{font-size:23px;line-height:1.18;margin-bottom:7px}
    .hero p{font-size:13px;line-height:1.5}
    .filter-panel{padding:10px;margin:12px 0 16px;border-radius:13px}
    input,select{height:42px;font-size:14px}
    .button{min-height:42px;font-size:13px;padding:0 14px}
    .section-header{margin:18px 0 10px}
    .section-header h2{font-size:20px}
    .updates{gap:10px}
    .update-card{padding:14px;border-radius:14px}
    .update-title{font-size:15px;line-height:1.35}
    .update-meta{font-size:11px}
    .badge{font-size:10px;padding:5px 8px}
    .ad-leaderboard{min-height:70px;margin:14px 0}
    .ad-inline{min-height:76px}
    .ad-sidebar{min-height:180px;margin:16px 0}
    .floating-ad{height:52px;bottom:6px}
    .floating-ad .ad-content{font-size:10px;padding:13px 28px 2px}
    .floating-ad-close{width:21px;height:21px;font-size:16px;line-height:19px}
}


/* Personalization */
.home-actions{display:flex;gap:10px;align-items:center}.button-secondary{background:#fff;color:#2f3b52;border:1px solid #dce2ec}.button-secondary:hover{background:#f4f6f9}.personalization-overlay{position:fixed;inset:0;background:rgba(15,23,42,.48);display:none;align-items:center;justify-content:center;padding:18px;z-index:9999}.personalization-overlay.show{display:flex}.personalization-modal{background:#fff;width:min(620px,100%);max-height:88vh;overflow:auto;border-radius:22px;padding:26px;box-shadow:0 24px 80px rgba(0,0,0,.25)}.personalization-modal h2{margin:0 0 8px;color:#172033}.personalization-modal p{margin:0 0 18px;color:#657086}.pref-group{margin:20px 0}.pref-group h3{margin:0 0 10px;font-size:15px;color:#253047}.pref-options{display:flex;flex-wrap:wrap;gap:8px}.pref-option{border:1px solid #dce2ec;background:#fff;border-radius:999px;padding:8px 12px;cursor:pointer;font:inherit;font-size:13px}.pref-option.selected{background:#172033;color:#fff;border-color:#172033}.pref-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:24px;flex-wrap:wrap}.pref-link{border:0;background:transparent;color:#667085;padding:10px;cursor:pointer;font:inherit}.personalized-mode-note{display:none;margin:0 0 14px;padding:10px 13px;border-radius:10px;background:#f3f6fb;color:#3d4b63;font-size:13px}.personalized-mode-note.show{display:block}@media(max-width:600px){.home-actions{width:100%;justify-content:space-between}.personalization-modal{padding:20px;border-radius:18px}.pref-actions{justify-content:stretch}.pref-actions button{flex:1}}
</style>

</head>


<body data-page-type="{{ page_type }}">


<header>

    <div class="header-container">

        <a href="/" class="brand">

            <div class="logo" aria-label="MahaUpdate logo"><img src="data:image/png;base64,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" alt="MahaUpdate logo"></div>

            <div>

                <div class="brand-name"><span class="brand-maha">Maha</span><span class="brand-update">Update</span></div>

                <div class="brand-tagline">
                    Maharashtra Government Updates
                </div>

            </div>

        </a>


        <button
            class="mobile-menu-button"
            onclick="toggleMenu()"
        >
            ☰
        </button>


        <nav id="main-nav">
            <a href="/" class="{{ 'active' if active_page == 'home' }}">Home</a>
            <a href="/updates" class="{{ 'active' if active_page == 'updates' and not update_type }}">All Updates</a>
            <a href="/departments" class="{{ 'active' if active_page == 'departments' }}">Departments</a>
            <a href="/updates?type=Advertisement" class="{{ 'active' if update_type == 'Advertisement' }}">Recruitment</a>
            <a href="/updates?type=Result" class="{{ 'active' if update_type == 'Result' }}">Results</a>
            <a href="/updates?type=Hall Ticket" class="{{ 'active' if update_type == 'Hall Ticket' }}">Admit Cards</a>
            <a href="/about" class="{{ 'active' if active_page == 'about' }}">About</a>
        </nav>

    </div>

</header>


<main class="container">


{% if page_type == "home" %}

    <section class="hero">

        <h1>
            Never Miss an Important Government Update.
        </h1>

        <p>
            Recruitment, exams, results, admit cards and official notifications — all organized in one modern place.
        </p>

    </section>


    

    <div class="section-header">

        <h2>Latest Updates</h2>

        <div class="home-actions">
            <button type="button" class="button button-secondary" id="forYouButton">✨ For You</button>
            <a href="/updates" class="button">
                View All →
            </a>
        </div>

    </div>


{% elif page_type == "updates" %}

    <section class="hero">

        {% if selected_source %}
            <h1>{{ source_display_name(selected_source) }}{% if source_display_name(selected_source) != selected_source %} ({{ selected_source }}){% endif %} Updates</h1>
            <p>Latest official notifications, recruitment, results, admit cards and announcements from {{ source_display_name(selected_source) }}.</p>
        {% elif update_type == "Result" %}
            <h1>Government Results</h1>
            <p>Latest official examination, recruitment and selection results.</p>
        {% elif update_type == "Hall Ticket" %}
            <h1>Admit Cards & Hall Tickets</h1>
            <p>Official admit cards, call letters and examination hall tickets.</p>
        {% elif update_type == "Advertisement" %}
            <h1>Government Recruitment</h1>
            <p>Latest official recruitment notifications, vacancies and advertisements.</p>
        {% else %}
            <h1>All Government Updates</h1>
            <p>Search and filter official updates from Maharashtra government sources.</p>
        {% endif %}

    </section>


{% elif page_type == "mpsc" %}

    <section class="hero">

        <h1>MPSC Updates</h1>

        <p>
            Results, answer keys, merit lists, recruitment and official notifications.
        </p>

    </section>


{% elif page_type == "midc" %}

    <section class="hero">

        <h1>MIDC Updates</h1>

        <p>
            Latest Maharashtra Industrial Development Corporation updates and notifications.
        </p>

    </section>


{% elif page_type == "departments" %}

<section class="department-showcase">
        <div class="section-header">
            <div>
                <h1 style="margin:0">All Departments</h1>
                <p class="section-subtitle">Browse updates source by source.</p>
            </div>
        </div>
        <div class="department-grid">
            {% for source in sources %}
            <a href="/updates?source={{ source | urlencode }}" class="department-chip">
                <span class="department-icon">
                    {% if source == 'MPSC' %}⚙
                    {% elif source == 'MIDC' %}🏭
                    {% elif 'Police' in source %}🛡
                    {% elif 'Forest' in source %}🌲
                    {% elif 'Railway' in source %}🚆
                    {% elif source == 'IBPS' %}🏦
                    {% elif 'TRANSCO' in source %}⚡
                    {% elif 'Jeevan' in source %}💧
                    {% elif 'NHM' in source or 'Health' in source %}❤
                    {% elif source == 'AAI' %}✈
                    {% elif source == 'UPSC' %}🏅
                    {% else %}🏛{% endif %}
                </span>
                <strong>{{ source }}</strong>
                <small>View updates →</small>
            </a>
            {% endfor %}
        </div>
    </section>

{% elif page_type == "about" %}

    <section class="hero">

        <h1>About MahaUpdate</h1>

        <p>
            One simple place to discover important Maharashtra government updates.
        </p>

    </section>


    <div class="about-card">

        <h2>What is MahaUpdate?</h2>

        <p>
            MahaUpdate is designed to make it easier to discover
            official Maharashtra government notifications,
            recruitment updates, results and important announcements.
        </p>

        <p>
            MahaUpdate does not replace official government websites.
            Every update includes a link to the original official source.
        </p>

        <p>
            Our goal is simple: help users find important updates
            without repeatedly checking multiple websites.
        </p>

    </div>


{% endif %}


{% if show_updates %}


    {% if show_filters %}

    <form method="get" class="filter-panel">

        <div class="filter-row">

            <input
                type="text"
                name="search"
                placeholder="Search exam, post, advertisement number..."
                value="{{ search }}"
            >


            <select name="source">

                <option value="">
                    All Sources
                </option>

                {% for value in sources %}

                <option
                    value="{{ value }}"
                    {{ 'selected' if value == selected_source }}
                >
                    {{ value }}
                </option>

                {% endfor %}

            </select>


            <select name="type">

                <option value="">
                    All Types
                </option>

                {% for value in types %}

                <option
                    value="{{ value }}"
                    {{ 'selected' if value == update_type }}
                >
                    {{ value }}
                </option>

                {% endfor %}

            </select>


            <button class="button" type="submit">
                Search
            </button>

        </div>


        {% if search or selected_source or update_type %}

        <a href="{{ current_path }}" class="clear-link">
            Clear filters
        </a>

        {% endif %}

    </form>

    {% endif %}


    <div class="section-header">

        <h2>
            {% if page_type == "home" %}
                Latest Updates
            {% else %}
                Updates
            {% endif %}
        </h2>

        <div class="count">
            {{ total_updates }} Updates
        </div>

    </div>

    <div class="personalized-mode-note" id="personalizedModeNote">✨ Showing updates matching your preferences first. <button type="button" class="pref-link" id="editPreferencesButton">Edit preferences</button></div>

    {% if updates %}

    <section class="updates">


        {% for update in updates %}


            <article class="update-card" data-source="{{ update.source|e }}" data-type="{{ update.type|e }}">


                <div class="update-top">

                    <div class="badges">

                        <span class="
                            badge
                            {% if update.source == 'MPSC' %}
                                badge-mpsc
                            {% elif update.source == 'MIDC' %}
                                badge-midc
                            {% else %}
                                badge-source
                            {% endif %}
                        ">
                            {{ update.source }}
                        </span>


                        <span class="badge badge-type">
                            {{ update.type }}
                        </span>

                    </div>


                    <span class="date">
                        {{ format_date(update.first_seen) }}
                    </span>

                </div>


                <h3>
                    {{ update.title }}
                </h3>


                {% if update.source == "IBPS" and (update.official_url|lower in ["https://www.ibps.in", "https://www.ibps.in/", "http://www.ibps.in", "http://www.ibps.in/"]) %}
                <a
                    href="/go?url={{ update.official_url | urlencode }}&title={{ update.title | urlencode }}&source=IBPS"
                    class="official-button"
                    title="Open the official IBPS search page for this notification"
                >
                    View Official Notification →
                </a>
                {% else %}
                <a
                    href="/go?url={{ update.official_url | urlencode }}&source={{ update.source | urlencode }}"
                    class="official-button"
                >
                    View Official Update →
                </a>
                {% endif %}


            </article>


            {% if loop.index == 3 and loop.index < updates|length %}

            <div class="ad-large">

                <div class="ad-label">
                    Advertisement
                </div>

                <strong>
                    Advertisement
                </strong>

                <span>
                    Advertisement will appear here
                </span>

            </div>

            {% endif %}


            {% if loop.index == 7 and loop.index < updates|length %}

            <div class="ad-large">

                <div class="ad-label">
                    Advertisement
                </div>

                <strong>
                    Advertisement
                </strong>

                <span>
                    Advertisement will appear here
                </span>

            </div>

            {% endif %}


        {% if loop.index % 6 == 0 %}
        <div class="ad-slot ad-inline">
            <div class="ad-content">Responsive Inline Advertisement<br><small>Advertisement space</small></div>
        </div>
        {% endif %}
        {% endfor %}


    </section>


    {% else %}

        <div class="empty">

            <h3>No updates found</h3>

            <p>
                Try changing your search or filters.
            </p>

        </div>

    {% endif %}


    {% if total_pages > 1 %}

    <div class="pagination">


        {% if page > 1 %}

        <a href="{{ pagination_url(page - 1) }}">
            ←
        </a>

        {% endif %}


        {% for number in pagination_items %}
            {% if number is none %}
                <span class="pagination-ellipsis">…</span>
            {% elif number == page %}
                <span class="current">{{ number }}</span>
            {% else %}
                <a href="{{ pagination_url(number) }}">{{ number }}</a>
            {% endif %}
        {% endfor %}


        {% if page < total_pages %}

        <a href="{{ pagination_url(page + 1) }}">
            →
        </a>

        {% endif %}


    </div>

    {% endif %}


{% endif %}


<div class="ad-slot ad-sidebar"><div class="ad-content">Advertisement<br><small>300 × 250</small></div></div>
</main>


<div class="floating-ad" id="floatingAd">
    <div class="ad-label">ADVERTISEMENT</div>
    <div class="ad-content">728 × 90 Responsive Banner Advertisement</div>
    <button class="floating-ad-close" onclick="document.getElementById('floatingAd').remove()" aria-label="Close">×</button>
</div>


<div class="personalization-overlay" id="personalizationOverlay" aria-hidden="true">
  <div class="personalization-modal" role="dialog" aria-modal="true" aria-labelledby="personalizationTitle">
    <h2 id="personalizationTitle">Make MahaUpdate yours</h2>
    <p>Choose what you care about. We will use these preferences to prioritize relevant updates on this device.</p>
    <div class="pref-group"><h3>Departments</h3><div class="pref-options" id="sourcePreferences"></div></div>
    <div class="pref-group"><h3>Update types</h3><div class="pref-options" id="typePreferences"></div></div>
    <div class="pref-actions"><button type="button" class="pref-link" id="maybeLaterButton">Maybe later</button><button type="button" class="button" id="savePreferencesButton">Personalize My Updates</button></div>
  </div>
</div>

<footer>

    <strong>MahaUpdate</strong>

    <br>

    Latest updates from official Maharashtra government sources.

</footer>


<script>
function toggleMenu(){document.getElementById("main-nav").classList.toggle("open");}
(function(){
 const KEY="mahaupdate_preferences_v1", DISMISS="mahaupdate_preferences_dismissed_v1";
 const overlay=document.getElementById("personalizationOverlay"), srcBox=document.getElementById("sourcePreferences"), typeBox=document.getElementById("typePreferences");
 const cards=()=>Array.from(document.querySelectorAll(".update-card"));

// Get ALL available departments and update types from Flask/Supabase,
// not only from the currently visible update cards.
const sources = {{ sources|tojson }};
const types = {{ types|tojson }};
 function load(){try{return JSON.parse(localStorage.getItem(KEY))||{sources:[],types:[]};}catch(e){return {sources:[],types:[]};}}
 function chip(value,box,selected){const b=document.createElement("button");b.type="button";b.className="pref-option"+(selected.includes(value)?" selected":"");b.textContent=value;b.dataset.value=value;b.onclick=()=>b.classList.toggle("selected");box.appendChild(b);}
 function render(){const p=load();srcBox.innerHTML="";typeBox.innerHTML="";sources.forEach(v=>chip(v,srcBox,p.sources||[]));types.forEach(v=>chip(v,typeBox,p.types||[]));}
 function openPrefs(){render();overlay.classList.add("show");overlay.setAttribute("aria-hidden","false");}
 function closePrefs(){overlay.classList.remove("show");overlay.setAttribute("aria-hidden","true");}
 function getSelected(box){return Array.from(box.querySelectorAll(".pref-option.selected")).map(x=>x.dataset.value);}
 function applyForYou(){const p=load(), list=document.querySelector(".updates"), note=document.getElementById("personalizedModeNote");if(!list)return false;if(!(p.sources||[]).length && !(p.types||[]).length){openPrefs();return false;}const ordered=cards().map((c,i)=>({c,i,score:((p.sources||[]).includes(c.dataset.source)?2:0)+((p.types||[]).includes(c.dataset.type)?1:0)})).sort((a,b)=>b.score-a.score||a.i-b.i);ordered.forEach(x=>list.appendChild(x.c));if(note)note.classList.add("show");return true;}
 document.getElementById("savePreferencesButton").onclick=()=>{localStorage.setItem(KEY,JSON.stringify({sources:getSelected(srcBox),types:getSelected(typeBox)}));localStorage.removeItem(DISMISS);closePrefs();applyForYou();};
 document.getElementById("maybeLaterButton").onclick=()=>{localStorage.setItem(DISMISS,"1");closePrefs();};
 const edit=document.getElementById("editPreferencesButton");if(edit)edit.onclick=openPrefs;
 const forYou=document.getElementById("forYouButton");if(forYou)forYou.onclick=applyForYou;
 let clicks=0, timer=setTimeout(()=>{if(!localStorage.getItem(KEY)&&!localStorage.getItem(DISMISS))openPrefs();},60000);
 document.addEventListener("click",e=>{if(e.target.closest(".official-button")){clicks++;if(clicks>=3&&!localStorage.getItem(KEY)&&!localStorage.getItem(DISMISS)){clearTimeout(timer);openPrefs();}}});
 if(localStorage.getItem(KEY)){setTimeout(()=>{if(document.body.dataset.pageType==="home")applyForYou();},0);}
})();
</script>



<!-- BUILD: TOP-LEADERBOARD-REMOVED-BOTTOM-FLOATING-KEPT -->
</body>

</html>
"""

# Reuse the existing header branding for the favicon, avoiding a separate
# static-file path that could fail in the Render/Linux deployment.
LOGO_DATA_URI = re.search(
    r'<img src="(data:image/png;base64,[^"]+)" alt="MahaUpdate logo">', PAGE
).group(1)


# ============================================================
# HELPERS
# ============================================================

def get_supabase():

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise Exception(
            "SUPABASE_URL and SUPABASE_KEY must be set."
        )

    return create_client(url, key)



_FILTER_CACHE = {"expires": 0.0, "sources": [], "types": []}
FILTER_CACHE_SECONDS = 60

def invalidate_filter_cache():
    """Call after ingestion when a new source or type may have been inserted."""
    _FILTER_CACHE["expires"] = 0.0

def get_filter_options():
    now = monotonic()
    if now < _FILTER_CACHE["expires"]:
        return _FILTER_CACHE["sources"], _FILTER_CACHE["types"]

    supabase = get_supabase()
    response = supabase.table("updates").select("source,type,title").range(
        0, VALID_UPDATE_CANDIDATE_LIMIT - 1
    ).execute()
    rows = [
        row for row in (response.data or [])
        if is_valid_notification_title(row.get("title"))
    ]
    sources = sorted({row.get("source") for row in rows if row.get("source")})
    types = sorted({row.get("type") for row in rows if row.get("type")})
    _FILTER_CACHE.update({
        "expires": now + FILTER_CACHE_SECONDS,
        "sources": sources,
        "types": types,
    })
    return sources, types

def get_search_updates_from_db(search="", selected_source="", update_type="", page=1, per_page=12):
    """Database search first, then typo-tolerant fallback on a capped candidate set."""
    supabase = get_supabase()
    variants, seen = [], set()
    for variant in search_variants(search):
        value = " ".join(str(variant).split()).strip()
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            variants.append(value)

    if not variants:
        return [], 0

    clauses = []
    for variant in variants[:12]:
        value = variant.replace(",", " ")
        clauses += [
            f"title.ilike.%{value}%",
            f"source.ilike.%{value}%",
            f"type.ilike.%{value}%"
        ]

    base = supabase.table("updates").select(
        "source,title,type,first_seen,official_url", count="exact"
    ).or_(",".join(clauses))

    if selected_source:
        base = base.eq("source", selected_source)
    if update_type:
        base = base.eq("type", update_type)

    direct_rows = get_valid_rows(base)
    direct_total = len(direct_rows)

    # Literal/alias search succeeded: keep the fast database path.
    if direct_total:
        return page_of_rows(direct_rows, page, per_page), direct_total

    # Typo fallback: fetch a capped recent candidate set, then use the existing
    # smart_match() similarity logic. This handles firemn -> fireman without
    # loading the entire table.
    fallback = supabase.table("updates").select(
        "source,title,type,first_seen,official_url"
    )
    if selected_source:
        fallback = fallback.eq("source", selected_source)
    if update_type:
        fallback = fallback.eq("type", update_type)

    candidates = get_valid_rows(fallback)

    matches = [item for item in candidates if is_valid_notification_title(item.get("title")) and smart_match(search, item)]
    matches.sort(key=lambda item: item.get("first_seen") or "", reverse=True)

    total = len(matches)
    return page_of_rows(matches, page, per_page), total

def get_valid_rows(query):
    """Read candidates, reject junk, then let callers paginate valid records."""
    response = query.order("first_seen", desc=True).range(
        0, VALID_UPDATE_CANDIDATE_LIMIT - 1
    ).execute()
    return [
        row for row in (response.data or [])
        if is_valid_notification_title(row.get("title"))
    ]


def page_of_rows(rows, page, per_page):
    start = max(0, (page - 1) * per_page)
    return rows[start:start + per_page]


def get_filtered_updates_from_db(selected_source="", update_type="", page=1, per_page=12):
    supabase = get_supabase()
    query = supabase.table("updates").select(
        "source,title,type,first_seen,official_url", count="exact"
    )
    if selected_source:
        query = query.eq("source", selected_source)
    if update_type:
        query = query.eq("type", update_type)
    rows = get_valid_rows(query)
    return page_of_rows(rows, page, per_page), len(rows)


def build_pagination_items(current, total):
    if total <= 9:
        return list(range(1, total + 1))
    pages = {1, total}
    pages.update(range(max(1, current - 2), min(total, current + 2) + 1))
    if current <= 4:
        pages.update(range(1, min(total, 5) + 1))
    if current >= total - 3:
        pages.update(range(max(1, total - 4), total + 1))
    ordered = sorted(pages)
    result, previous = [], None
    for number in ordered:
        if previous is not None and number - previous > 1:
            result.append(None)
        result.append(number)
        previous = number
    return result


SOURCE_NAMES = {
    "AAI": "Airport Authority of India",
    "MPSC": "Maharashtra Public Service Commission",
    "MIDC": "Maharashtra Industrial Development Corporation",
    "IBPS": "Institute of Banking Personnel Selection",
    "SSC": "Staff Selection Commission",
    "UPSC": "Union Public Service Commission",
    "MSEDCL": "Maharashtra State Electricity Distribution Company",
    "MAHATRANSCO": "Maharashtra State Electricity Transmission Company",
    "MAHAGENCO": "Maharashtra State Power Generation Company",
    "DMA": "Directorate of Municipal Administration, Maharashtra",
    "PWD": "Public Works Department, Maharashtra",
    "NHM": "National Health Mission, Maharashtra",
    "MJP": "Maharashtra Jeevan Pradhikaran",
    "DMER": "Directorate of Medical Education and Research",
    "DFSL": "Directorate of Forensic Science Laboratories",
}

def source_display_name(source):
    source = str(source or "")
    return SOURCE_NAMES.get(source.upper(), source)

def format_date(value):

    if not value:
        return ""

    try:

        value = str(value).replace(
            "Z",
            "+00:00"
        )

        date = datetime.fromisoformat(value)

        now = datetime.now(date.tzinfo)

        difference = (
            now.date() - date.date()
        ).days

        if difference == 0:
            return "Today"

        if difference == 1:
            return "Yesterday"

        return date.strftime("%d %b %Y")

    except Exception:

        return str(value)[:10]


def get_page_number():

    try:
        page = int(request.args.get("page", 1))

        if page < 1:
            page = 1

        return min(page, MAX_PAGE_NUMBER)

    except ValueError:
        return 1


SEARCH_ALIASES = {
    "fireman": ["फायरमन", "अग्निशमन", "fire man", "fire-man"],
    "fire man": ["fireman", "फायरमन", "अग्निशमन"],
    "police bharti": ["पोलीस भरती", "police recruitment"],
    "police": ["पोलीस", "police"],
    "bharti": ["भरती", "recruitment", "vacancy"],
    "recruitment": ["भरती", "vacancy", "recruitment"],
    "result": ["निकाल", "परिणाम", "result"],
    "hall ticket": ["प्रवेशपत्र", "admit card", "hallticket"],
    "admit card": ["प्रवेशपत्र", "hall ticket", "hallticket"],
    "exam": ["परीक्षा", "exam", "examination"],
    "engineer": ["अभियंता", "engineering", "engineer"],
    "driver": ["चालक", "driver"],
    "clerk": ["लिपिक", "clerk"],
    "nurse": ["परिचारिका", "nursing", "nurse"],
    "forest guard": ["वनरक्षक", "forestguard"],
}

def normalize_search(value):
    value = unicodedata.normalize("NFKC", str(value or "")).lower()
    value = re.sub(r"[\W_]+", "", value, flags=re.UNICODE)
    return value

def search_variants(query):
    q = (query or "").strip().lower()
    variants = {q, normalize_search(q)}
    for key, values in SEARCH_ALIASES.items():
        if q == key or normalize_search(q) == normalize_search(key):
            variants.update(values)
    return {v for v in variants if v}

def smart_match(query, update):
    if not query:
        return True

    title = str(update.get("title", ""))
    source = str(update.get("source", ""))
    update_type = str(update.get("type", ""))
    haystack = " ".join([title, source, update_type]).lower()
    normalized_haystack = normalize_search(haystack)

    # Exact substring and spacing/punctuation-insensitive matching.
    for variant in search_variants(query):
        if variant.lower() in haystack:
            return True
        if normalize_search(variant) and normalize_search(variant) in normalized_haystack:
            return True

    # Token match for multi-word English searches.
    tokens = [normalize_search(t) for t in re.split(r"\s+", query) if normalize_search(t)]
    if tokens and all(token in normalized_haystack for token in tokens):
        return True

    # Predictable fuzzy fallback: every significant query token must match.
    query_tokens = [normalize_search(x) for x in re.findall(r"\w+", query, flags=re.UNICODE)]
    words = [normalize_search(x) for x in re.findall(r"\w+", haystack, flags=re.UNICODE)]
    significant = [x for x in query_tokens if len(x) >= 4]
    if significant:
        for token in significant:
            threshold = 0.80 if len(token) >= 7 else 0.84
            if not any(SequenceMatcher(None, token, word).ratio() >= threshold for word in words if word):
                return False
        return True
    return False


def paginate(items, page):

    total_items = len(items)

    total_pages = max(
        1,
        (total_items + UPDATES_PER_PAGE - 1)
        // UPDATES_PER_PAGE
    )

    if page > total_pages:
        page = total_pages

    start = (
        page - 1
    ) * UPDATES_PER_PAGE

    end = (
        start + UPDATES_PER_PAGE
    )

    return (
        items[start:end],
        total_items,
        total_pages,
        page
    )


def render_page(
    page_type,
    page_title,
    active_page,
    fixed_source=None,
    home=False,
    show_filters=True
):
    try:
        sources, types = get_filter_options()

        search = request.args.get("search", "").strip()
        selected_source = fixed_source or request.args.get("source", "").strip()
        update_type = request.args.get("type", "").strip()
        requested_page = get_page_number()

        if search:
            updates, total_updates = get_search_updates_from_db(search, selected_source, update_type, requested_page, UPDATES_PER_PAGE)
            total_pages = max(1, (total_updates + UPDATES_PER_PAGE - 1) // UPDATES_PER_PAGE)
            page = min(requested_page, total_pages)
        else:
            updates, total_updates = get_filtered_updates_from_db(
                selected_source=selected_source,
                update_type=update_type,
                page=requested_page,
                per_page=UPDATES_PER_PAGE,
            )
            total_pages = max(1, (total_updates + UPDATES_PER_PAGE - 1) // UPDATES_PER_PAGE)
            page = min(requested_page, total_pages)
            if requested_page != page and total_updates:
                updates, _ = get_filtered_updates_from_db(
                    selected_source=selected_source,
                    update_type=update_type,
                    page=page,
                    per_page=UPDATES_PER_PAGE,
                )

        if home:
            updates = updates[:12]
            total_pages = 1
            page = 1

        def pagination_url(number):
            params = []
            if search:
                params.append("search=" + quote(search))
            if selected_source and not fixed_source:
                params.append("source=" + quote(selected_source))
            if update_type:
                params.append("type=" + quote(update_type))
            params.append("page=" + str(number))
            return request.path + "?" + "&".join(params)

        return render_template_string(
            PAGE, page_type=page_type, page_title=page_title, active_page=active_page,
            show_updates=(page_type != "about"), show_filters=show_filters,
            updates=updates, total_updates=total_updates, total_pages=total_pages,
            page=page, pagination_items=build_pagination_items(page, total_pages),
            sources=sources, types=types, search=search,
            selected_source="" if fixed_source else selected_source,
            update_type=update_type, current_path=request.path,
            pagination_url=pagination_url, format_date=format_date,
            source_display_name=source_display_name, logo_data_uri=LOGO_DATA_URI,
        )
    except Exception:
        app.logger.exception("MahaUpdate render failure")
        return render_template_string(
            "<h2>Something went wrong</h2><p>Please try again later.</p>"
        ), 500

# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def home():

    return render_page(

        page_type="home",

        page_title="MahaUpdate",

        active_page="home",

        home=True,

        show_filters=True

    )


@app.route("/updates")
def updates_page():

    return render_page(

        page_type="updates",

        page_title="All Updates",

        active_page="updates"

    )


@app.route("/mpsc")
def mpsc_page():

    return render_page(

        page_type="mpsc",

        page_title="MPSC Updates",

        active_page="mpsc",

        fixed_source="MPSC"

    )


@app.route("/midc")
def midc_page():

    return render_page(

        page_type="midc",

        page_title="MIDC Updates",

        active_page="midc",

        fixed_source="MIDC"

    )


@app.route("/departments")
def departments_page():
    try:
        sources, types = get_filter_options()
    except Exception:
        app.logger.exception("Departments load failure")
        return "<h2>Something went wrong</h2><p>Please try again later.</p>", 500

    return render_template_string(
        PAGE,
        page_type="departments",
        page_title="All Departments",
        active_page="departments",
        show_updates=False,
        logo_data_uri=LOGO_DATA_URI,
        show_filters=False,
        updates=[],
        total_updates=0,
        total_pages=1,
        page=1,
        sources=sources,
        types=types,
        search="",
        selected_source="",
        update_type="",
        current_path=request.path,
        pagination_url=lambda n: "/departments",
        format_date=format_date,
        source_display_name=source_display_name,
        pagination_items=[]
    )

@app.route("/about")
def about_page():

    return render_page(

        page_type="about",

        page_title="About",

        active_page="about",

        show_filters=False

    )


# ============================================================
# INTERNAL OFFICIAL LINK ROUTE
# ============================================================


# Canonical source names keep redirect validation strict while supporting
# the display names actually stored in the updates.source column.
SOURCE_ALIASES = {
    "MPSC": "MPSC",
    "MIDC": "MIDC",
    "IBPS": "IBPS",
    "SSC": "SSC",
    "UPSC": "UPSC",
    "AAI": "AAI",
    "MSEDCL": "MSEDCL",
    "MAHATRANSCO": "MAHATRANSCO",
    "MAHAGENCO": "MAHAGENCO",
    "MJP": "MJP",
    "MAHARASHTRA JEEVAN PRADHIKARAN": "MJP",
    "PWD": "PWD",
    "NHM": "NHM",
    "NHM MAHARASHTRA": "NHM",
    "NATIONAL HEALTH MISSION": "NHM",
    "DMA": "DMA",
    "DMA MAHARASHTRA": "DMA",
    "DIRECTORATE OF MUNICIPAL ADMINISTRATION": "DMA",
    "DMER": "DMER",
    "DMER MAHARASHTRA": "DMER",
    "DIRECTORATE OF MEDICAL EDUCATION AND RESEARCH": "DMER",
    "DFSL": "DFSL",
    "DFSL MAHARASHTRA": "DFSL",
    "DIRECTORATE OF FORENSIC SCIENCE LABORATORIES": "DFSL",
    "INDIAN RAILWAYS": "INDIAN RAILWAYS",
    "RAILWAY": "INDIAN RAILWAYS",
    "MAHARASHTRA POLICE": "MAHARASHTRA POLICE",
    "POLICE": "MAHARASHTRA POLICE",
    "PUBLIC HEALTH DEPARTMENT": "PUBLIC HEALTH DEPARTMENT",
    "FOREST": "FOREST",
    "FOREST DEPARTMENT": "FOREST",
    "WCD": "WCD",
    "WOMEN AND CHILD DEVELOPMENT": "WCD",
    "SAINIK WELFARE": "SAINIK WELFARE",
    "MAHARASHTRA SAINIK WELFARE": "SAINIK WELFARE",
}

OFFICIAL_DOMAINS = {
    "MPSC": ("mpsc.gov.in",),
    "MIDC": ("midcindia.org",),
    "IBPS": ("ibps.in", "ibpsreg.ibps.in"),
    "SSC": ("ssc.gov.in",),
    "UPSC": ("upsc.gov.in",),
    "AAI": ("aai.aero",),
    "MSEDCL": ("mahadiscom.in",),
    "MAHATRANSCO": ("mahatransco.in",),
    "MAHAGENCO": ("mahagenco.in",),
    "MJP": ("mjp.maharashtra.gov.in",),
    "PWD": ("mahapwd.gov.in", "cdnbbsr.s3waas.gov.in"),
    "NHM": ("arogya.maharashtra.gov.in", "nhm.maharashtra.gov.in", "cdnbbsr.s3waas.gov.in"),
    "DMA": ("mahadma.maharashtra.gov.in",),
    "DMER": ("dmer.maharashtra.gov.in",),
    "DFSL": ("dfsl.maharashtra.gov.in",),
    "INDIAN RAILWAYS": ("indianrailways.gov.in", "rrbcdg.gov.in"),
    "MAHARASHTRA POLICE": ("mahapolice.gov.in",),
    "PUBLIC HEALTH DEPARTMENT": ("arogya.maharashtra.gov.in", "cdnbbsr.s3waas.gov.in"),
    "FOREST": ("mahaforest.gov.in",),
    "WCD": ("womenchild.maharashtra.gov.in",),
    "SAINIK WELFARE": ("mahasainik.maharashtra.gov.in", "maharashtra.gov.in"),
}

def normalize_source(source):
    normalized = " ".join(str(source or "").upper().split())
    return SOURCE_ALIASES.get(normalized, normalized)

def host_matches_allowed(host, allowed_domains):
    host = (host or "").lower().rstrip(".")
    return any(host == domain or host.endswith("." + domain) for domain in allowed_domains)

def validate_official_url(url, source):
    parsed = urlparse(str(url or ""))
    # HTTPS only. Add a legacy exception here only if a real official source
    # demonstrably still requires HTTP.
    if parsed.scheme != "https" or not parsed.netloc:
        return False

    canonical_source = normalize_source(source)
    allowed_domains = OFFICIAL_DOMAINS.get(canonical_source, ())
    return bool(allowed_domains) and host_matches_allowed(
        parsed.hostname, allowed_domains
    )

def unmapped_known_sources(sources):
    """Return source labels that are not covered by the redirect mapping."""
    return sorted({
        str(source) for source in sources
        if str(source).strip()
        and normalize_source(source) not in OFFICIAL_DOMAINS
    })

@app.route("/go")
def go_to_official():
    url = unquote(request.args.get("url", "") or "")
    title = unquote(request.args.get("title", "") or "")
    source = request.args.get("source", "") or ""

    # Legacy IBPS rows may contain only the IBPS homepage. Keep the fallback
    # on the official HTTPS site instead of sending users to a generic page.
    ibps_home_urls = {
        "https://www.ibps.in",
        "https://www.ibps.in/",
    }
    if (
        normalize_source(source) == "IBPS"
        and url.rstrip("/") in {item.rstrip("/") for item in ibps_home_urls}
        and title
    ):
        from urllib.parse import quote_plus
        return redirect("https://www.ibps.in/?s=" + quote_plus(title))

    if not validate_official_url(url, source):
        app.logger.warning(
            "Blocked invalid official redirect source=%r url=%r",
            source, url
        )
        return redirect("/updates")

    return redirect(url)


@app.route("/health")
def health():
    try:
        response = (
            get_supabase()
            .table("updates")
            .select("source")
            .limit(1)
            .execute()
        )
        _ = response.data
        return {"status": "ok"}, 200
    except Exception:
        app.logger.warning("Health check database unavailable")
        return {"status": "unavailable"}, 503


@app.after_request
def add_security_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
        "connect-src 'self' https:; frame-ancestors 'self'; "
        "base-uri 'self'; form-action 'self'"
    )
    return response

# Production: add indexes on first_seen and (source, type, first_seen); for very large datasets use PostgreSQL FTS + GIN index.
# Deploy behind a production WSGI server/reverse proxy and keep SUPABASE_KEY server-only.

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=False

    )
