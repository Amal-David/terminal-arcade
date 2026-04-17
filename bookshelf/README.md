# The Bookshelf

A terminal book discovery and collection manager with 313 curated books, integrated quotes, and reading lists.

![Browse](../assets/screenshots/bookshelf_browse.png)

## Run

```bash
# From the repo root
python3 -m bookshelf

# Or install and run anywhere
pip install -e .
bookshelf
```

## Controls

| Key | Action |
|---|---|
| `Up` / `Down` / `j` / `k` | Navigate books |
| `Enter` / `Right` | Open selected book |
| `Esc` / `Left` / `q` | Back / Quit |
| `PgUp` / `PgDn` | Page up / down |
| `Tab` / `Shift+Tab` | Cycle genre filter or collection tabs |
| `/` | Search |
| `c` | Open collection |
| `r` | Pick a random book |
| `f` | Toggle favorite |
| `Left` / `Right` / `n` / `p` | Browse quotes (detail screen) |
| `m` | Mark as read |
| `w` | Want to read |
| `?` | Show help overlay |

## Screens

### Shelf (Main Browse)

Browse all 313 books filtered by genre. Genre tabs at the top show counts for All, Motivation, Startup, and Romance.

### Book Detail

View a book's summary, mood tags, and quotes. Scroll through quotes with left/right arrows. Mark books as favorites, read, or want-to-read.

![Book Detail](../assets/screenshots/bookshelf_detail.png)

### Search

Live search by title or author with real-time filtering and result counts.

### Collection

Manage your reading lists across four tabs:

- **Favorites** — Books you've hearted
- **Read** — Books you've finished
- **Want to Read** — Your wishlist
- **Stats** — Books explored, quotes seen, and library totals

## Library

313 books across 3 genres:

| Genre | Books | Icon |
|---|---|---|
| Motivation | 132 | ★ |
| Startup | 99 | ◆ |
| Romance | 82 | ♥ |

Each book includes mood tags (e.g. "hustle mode", "cozy night", "fresh start") and the quote catalog has 2,500+ quotes with context tags.

## Persistence

Reading lists and stats are saved to `~/.config/bookshelf/state.json`. Optional preferences can be set in `~/.config/bookshelf/config.json`.

## License

[MIT](../LICENSE)
