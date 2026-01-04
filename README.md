# Mantooth - Personal Blog

**Live site: [mantooth.me](https://mantooth.me)**

A personal blog website with travel stories, lifestyle content, and more.

## Structure

```
website/
├── index.html              # Homepage
├── blogs.html              # Blog listing with tag filtering
├── about.html              # About page
├── contact.html            # Contact page
├── assets/
│   ├── css/style.css       # Styles
│   ├── js/                 # Interactive features
│   │   ├── tag-filter.js   # Tag filtering
│   │   ├── recent-posts.js # Homepage recent posts
│   │   ├── image-optimizer.js # Lazy loading
│   │   └── clickable-cards.js # Card interactions
│   ├── data/blog-data.json # Blog metadata
│   └── images/             # Site images
└── blog-processor/
    ├── input/              # Source PDFs (11 blogs)
    ├── images/             # Blog featured images
    └── output/             # Generated blog HTML files
```

## Blog Content

The blog posts are stored as:
- **Source PDFs** in `blog-processor/input/` - the original written content
- **HTML pages** in `blog-processor/output/` - the web-ready versions
- **Metadata** in `assets/data/blog-data.json` - titles, tags, excerpts

## Deployment

Hosted on GitHub Pages with automatic deployment via `.github/workflows/deploy.yml`.

Domain: mantooth.me (configured via `website/CNAME`)
