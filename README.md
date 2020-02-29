
# Clog

Clog is a home-grown static site generator in Python.

## Installation 

```bash
pip install clog
```

## Usage

```bash
Usage: clog [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  build    Converts Markdown sources to HTML pages
  deploy   Deploys site to GitHub pages
  develop  Preview site using live-server
  new      Create a new site
```

## Additional Information

The directory structure of a new site:

```
.
├── config.yaml
├── content
├── layouts
├── static
└── themes
```

##### `content`

Contains written information written in markdown (e.g. a blog post).

##### `layouts`

Provides extra layouts that are not provided with the theme, which is important when you're trying to make a custom page such as a portfolio page. An example using this feature will be given later on.

##### `static`

Static contains files such as css, javascript, and images.

##### `config.yaml`

Configuration file for the site.

### ✍🏽 Add some content

Manually create content files in `content/posts/` directory. Markdown files created directly in the `content` directory become top-level pages for the site.

The file should start with this:

```yaml
---
title: "Hello World"
date: 2020-02-29T01:02:03+01:00
---
```

### 🚀 Start the Clog server

```
clog develop
```

### 🏗️ Build static pages

Running the command below will place publishable content in `./public` directory.

```
clog build
```

### 🏁 Deploying to GitHub Pages

```bash
clog deploy --autocommit
```
```
