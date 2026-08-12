CREATE TABLE IF NOT EXISTS articles (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  slug TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'write' CHECK(kind IN ('write','film','photo','code','music')),
  language TEXT NOT NULL DEFAULT 'en',
  summary TEXT NOT NULL DEFAULT '',
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','published','deleted')),
  source_url TEXT NOT NULL DEFAULT '',
  image_url TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  published_at TEXT,
  UNIQUE(language, kind, slug)
);
CREATE INDEX IF NOT EXISTS articles_public_idx ON articles(status, published_at DESC);
CREATE INDEX IF NOT EXISTS articles_kind_idx ON articles(kind, status, published_at DESC);
