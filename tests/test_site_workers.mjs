import assert from "node:assert/strict";
import test from "node:test";

import bookshelfWorker, {
  acceptsMarkdown as bookshelfAcceptsMarkdown,
} from "../sites/bookshelf/_worker.js";
import polyglotWorker, {
  acceptsMarkdown as polyglotAcceptsMarkdown,
} from "../sites/polyglot/_worker.js";

const workers = [
  ["Bookshelf", bookshelfWorker, bookshelfAcceptsMarkdown],
  ["Polyglot", polyglotWorker, polyglotAcceptsMarkdown],
];

for (const [name, worker, acceptsMarkdown] of workers) {
  test(`${name} honors Markdown Accept quality values`, async () => {
    assert.equal(acceptsMarkdown("text/markdown"), true);
    assert.equal(acceptsMarkdown("text/html, text/markdown; q=0.5"), true);
    assert.equal(acceptsMarkdown("text/markdown;q=0"), false);
    assert.equal(acceptsMarkdown("text/html"), false);

    const assets = {
      fetch(request) {
        const pathname = new URL(request.url).pathname;
        return Promise.resolve(new Response(pathname));
      },
    };
    const response = await worker.fetch(
      new Request("https://example.test/", {
        headers: { Accept: "text/markdown;q=0" },
      }),
      { ASSETS: assets },
    );

    assert.equal(await response.text(), "/");
    assert.match(response.headers.get("Vary"), /Accept/);
  });
}
