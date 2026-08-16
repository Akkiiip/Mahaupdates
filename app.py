import os
from datetime import datetime
from urllib.parse import quote, unquote

from flask import Flask, render_template_string, request, redirect
from supabase import create_client


app = Flask(__name__)


# ============================================================
# CONFIG
# ============================================================

UPDATES_PER_PAGE = 10


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

            max-width: 1150px;

            margin: auto;

            padding: 14px 20px;

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

            width: 44px;

            height: 44px;

            border-radius: 12px;

            background: var(--saffron);

            display: flex;

            justify-content: center;

            align-items: center;

            position: relative;

        }


        .logo::before {

            content: "";

            width: 17px;

            height: 21px;

            border-left: 5px solid var(--navy);

            border-right: 5px solid var(--navy);

            transform: skewX(-10deg);

        }


        .brand-name {

            font-size: 22px;

            font-weight: 800;

            letter-spacing: -.4px;

        }


        .brand-tagline {

            font-size: 11px;

            color: #b8c4d5;

            margin-top: 2px;

        }


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

            max-width: 1100px;

            margin: auto;

            padding: 30px 20px 50px;

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

    </style>

</head>


<body>


<header>

    <div class="header-container">

        <a href="/" class="brand">

            <div class="logo"></div>

            <div>

                <div class="brand-name">
                    MahaUpdate
                </div>

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

            <a href="/"
               class="{{ 'active' if active_page == 'home' }}">
                Home
            </a>

            <a href="/updates"
               class="{{ 'active' if active_page == 'updates' }}">
                All Updates
            </a>

            <a href="/mpsc"
               class="{{ 'active' if active_page == 'mpsc' }}">
                MPSC
            </a>

            <a href="/midc"
               class="{{ 'active' if active_page == 'midc' }}">
                MIDC
            </a>

            <a href="/about"
               class="{{ 'active' if active_page == 'about' }}">
                About
            </a>

        </nav>

    </div>

</header>


<main class="container">


{% if page_type == "home" %}

    <section class="hero">

        <h1>
            Maharashtra Government Updates, Simplified.
        </h1>

        <p>
            Stay updated with official notifications, results,
            answer keys, recruitment updates and important announcements.
        </p>

    </section>


    <div class="source-grid">

        <a href="/mpsc" class="source-card">

            <h3>MPSC</h3>

            <p>
                Maharashtra Public Service Commission updates,
                results, answer keys and notifications.
            </p>

        </a>


        <a href="/midc" class="source-card">

            <h3>MIDC</h3>

            <p>
                Maharashtra Industrial Development Corporation
                recruitment and official updates.
            </p>

        </a>

    </div>


    <div class="section-header">

        <h2>Latest Updates</h2>

        <a href="/updates" class="button">
            View All →
        </a>

    </div>


{% elif page_type == "updates" %}

    <section class="hero">

        <h1>All Government Updates</h1>

        <p>
            Search and filter official updates from Maharashtra government sources.
        </p>

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


    {% if updates %}

    <section class="updates">


        {% for update in updates %}


            <article class="update-card">


                <div class="update-top">

                    <div class="badges">

                        <span class="
                            badge
                            {% if update.source == 'MPSC' %}
                                badge-mpsc
                            {% else %}
                                badge-midc
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


                <a
                    href="/go?url={{ update.official_url | urlencode }}"
                    class="official-button"
                >
                    View Official Update →
                </a>


            </article>


            {% if loop.index == 3 and loop.index < updates|length %}

            <div class="ad-large">

                <div class="ad-label">
                    Advertisement
                </div>

                <strong>
                    Large Ad Space
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
                    Large Ad Space
                </strong>

                <span>
                    Advertisement will appear here
                </span>

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


        {% for number in range(1, total_pages + 1) %}

            {% if number == page %}

                <span class="current">
                    {{ number }}
                </span>

            {% else %}

                <a href="{{ pagination_url(number) }}">
                    {{ number }}
                </a>

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


</main>


<footer>

    <strong>MahaUpdate</strong>

    <br>

    Latest updates from official Maharashtra government sources.

</footer>


<script>

    function toggleMenu() {

        document
            .getElementById("main-nav")
            .classList
            .toggle("open");

    }

</script>


</body>

</html>
"""


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


def get_all_updates():

    supabase = get_supabase()

    response = (
        supabase
        .table("updates")
        .select(
            "source,title,type,first_seen,official_url"
        )
        .order(
            "first_seen",
            desc=True
        )
        .execute()
    )

    return response.data or []


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

        return page

    except ValueError:
        return 1


def filter_updates(
    updates,
    fixed_source=None
):

    search = request.args.get(
        "search",
        ""
    ).strip()

    selected_source = request.args.get(
        "source",
        ""
    )

    update_type = request.args.get(
        "type",
        ""
    )


    filtered = []

    for update in updates:

        if fixed_source:

            if update.get("source") != fixed_source:
                continue

        elif selected_source:

            if update.get("source") != selected_source:
                continue


        if update_type:

            if update.get("type") != update_type:
                continue


        if search:

            title = update.get(
                "title",
                ""
            ).lower()

            if search.lower() not in title:
                continue


        filtered.append(update)


    return (
        filtered,
        search,
        selected_source,
        update_type
    )


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

        all_updates = get_all_updates()

    except Exception as error:

        return f"""
        <h2>MahaUpdate Error</h2>
        <p>{error}</p>
        """, 500


    sources = sorted(
        {
            item.get("source")
            for item in all_updates
            if item.get("source")
        }
    )


    types = sorted(
        {
            item.get("type")
            for item in all_updates
            if item.get("type")
        }
    )


    if home:

        filtered = all_updates[:10]

        search = ""
        selected_source = ""
        update_type = ""

    else:

        (
            filtered,
            search,
            selected_source,
            update_type
        ) = filter_updates(
            all_updates,
            fixed_source
        )


    page = get_page_number()

    (
        updates,
        total_updates,
        total_pages,
        page
    ) = paginate(
        filtered,
        page
    )


    if home:

        total_pages = 1
        page = 1


    def pagination_url(number):

        params = []

        if search:
            params.append(
                "search=" + quote(search)
            )

        if selected_source and not fixed_source:
            params.append(
                "source=" + quote(selected_source)
            )

        if update_type:
            params.append(
                "type=" + quote(update_type)
            )

        params.append(
            "page=" + str(number)
        )

        query = "&".join(params)

        return request.path + "?" + query


    return render_template_string(

        PAGE,

        page_type=page_type,

        page_title=page_title,

        active_page=active_page,

        show_updates=(
            page_type != "about"
        ),

        show_filters=show_filters,

        updates=updates,

        total_updates=total_updates,

        total_pages=total_pages,

        page=page,

        sources=sources,

        types=types,

        search=search,

        selected_source=selected_source,

        update_type=update_type,

        current_path=request.path,

        pagination_url=pagination_url,

        format_date=format_date

    )


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

        show_filters=False

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

@app.route("/go")
def go_to_official():

    url = request.args.get(
        "url",
        ""
    )

    if not url:
        return redirect("/updates")

    url = unquote(url)

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):
        return redirect("/updates")

    return redirect(url)


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=False

    )