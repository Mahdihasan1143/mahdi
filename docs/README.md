# Ifada Solar — Website

A premium, fully responsive corporate website for **Ifada Electronics Ltd. (Ifada Solar)** —
Bangladesh's leading solar street light, panel, pump and inverter manufacturer since 2006.

## ✨ Features

- **Cinematic hero** with a scroll-driven **day → sunset → night** transition:
  the sun arcs across the sky and sets, stars and moon fade in, floating clouds,
  flying birds, swaying grass, reflecting solar panels, and a **solar street light
  that automatically turns on at night** — all pure CSS + vanilla JS.
- **Animated statistics** counters (years, projects, customers, MW, branches).
- **3D-hover product category** cards and featured product cards.
- **Why Choose Us**, **About**, **Solutions**, **Projects gallery**, **Process** timeline.
- **Auto-sliding customer reviews** carousel.
- **Solar Savings Calculator** — estimates monthly savings, required system size and ROI.
- **FAQ accordion**, **certifications**, **news/blog** section.
- **Contact section** with Google Map, click-to-call, WhatsApp, and a lead form that
  hands off to WhatsApp (no backend needed).
- Sticky navbar, scroll-progress bar, floating WhatsApp button, mobile menu.
- Fully **responsive** and respects `prefers-reduced-motion`.

## 🎨 Brand

| Token      | Value     |
|------------|-----------|
| Primary    | `#0B3D91` (Deep Blue) |
| Secondary  | `#FFC107` (Solar Yellow) |
| Accent     | `#00C853` (Green) |
| Background | `#F8FAFC` |
| Text       | `#1F2937` |
| Fonts      | Poppins (headings), Inter (body) |

## 🚀 Run locally

It's a static site — just open `index.html`, or serve the folder:

```bash
cd website
python3 -m http.server 8000
# then visit http://localhost:8000
```

## 🌐 Deploy (GitHub Pages)

1. Push this branch.
2. Repo **Settings → Pages** → Source: this branch, folder `/website`.
3. Your site goes live at `https://<user>.github.io/<repo>/`.

## 📁 Structure

```
website/
├── index.html      # all page sections
├── css/styles.css  # theme, layout, animations
├── js/script.js    # scroll effects, counters, slider, calculator, form
└── README.md
```

## 📞 Company details used

- **Ifada Electronics Ltd.** — solar solutions since 2006
- Head Office: House #89, Road #01, Block B, Kalshy Main Road, Pallabi, Mirpur-12, Dhaka-1216
- Phone: 01963 920520 · 01958 148100 · 01958 148101
- Email: ifadaelectronicsltd@gmail.com

> Statistics (projects, customers, MW, branches) are representative placeholders —
> replace them with official figures before going live.
