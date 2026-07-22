const MARKDOWN_ACCEPT = "text/markdown";
const SKILLS_PREFIX = "/.well-known/agent-skills/";
const PUBLIC_FILES = new Set(["/", "/robots.txt", "/sitemap.xml", "/llms.txt"]);
const DISCOVERY_LINKS = [
  '</llms.txt>; rel="describedby"; type="text/plain"',
  '</.well-known/agent-skills/index.json>; rel="describedby"; type="application/json"',
].join(", ");

export function acceptsMarkdown(header) {
  if (!header) return false;

  return header.split(",").some((range) => {
    const [mediaType, ...parameters] = range.trim().toLowerCase().split(";");
    if (mediaType.trim() !== MARKDOWN_ACCEPT) return false;

    const quality = parameters
      .map((parameter) => parameter.trim())
      .find((parameter) => parameter.startsWith("q="));
    if (!quality) return true;

    const value = Number(quality.slice(2));
    return Number.isFinite(value) && value > 0 && value <= 1;
  });
}

function decorate(response, { root }) {
  const decorated = new Response(response.body, response);
  decorated.headers.set("X-Content-Type-Options", "nosniff");
  decorated.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  if (root) {
    decorated.headers.set("Link", DISCOVERY_LINKS);
    decorated.headers.append("Vary", "Accept");
  }
  return decorated;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const root = url.pathname === "/";
    const wantsMarkdown = acceptsMarkdown(request.headers.get("Accept"));

    if (root && wantsMarkdown) {
      const markdownUrl = new URL("/llms.txt", url);
      const markdownResponse = await env.ASSETS.fetch(
        new Request(markdownUrl, { method: "GET", headers: request.headers }),
      );
      const decorated = decorate(markdownResponse, { root: true });
      decorated.headers.set("Content-Type", "text/markdown; charset=utf-8");
      return decorated;
    }

    if (url.pathname.startsWith(SKILLS_PREFIX)) {
      url.pathname = `/agent-skills/${url.pathname.slice(SKILLS_PREFIX.length)}`;
      const skillsResponse = await env.ASSETS.fetch(
        new Request(url, { method: "GET", headers: request.headers }),
      );
      return decorate(skillsResponse, { root: false });
    }

    if (
      !PUBLIC_FILES.has(url.pathname) &&
      !url.pathname.startsWith("/assets/") &&
      !url.pathname.startsWith("/agent-skills/")
    ) {
      return decorate(new Response("Not found", { status: 404 }), { root: false });
    }

    return decorate(await env.ASSETS.fetch(request), { root });
  },
};
