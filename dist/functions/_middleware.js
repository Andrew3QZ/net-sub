
export async function onRequest(context) {
  const req = context.request;
  const env = context.env || {};
  const url = new URL(req.url);
  const secret = env.SUB_PATH_SECRET || '';

  if (!secret) {
    return new Response('Not Found', { status: 404 });
  }

  const prefix = `/sub/${secret}/`;
  if (!url.pathname.startsWith(prefix)) {
    return new Response('Not Found', { status: 404 });
  }

  url.pathname = '/' + url.pathname.slice(prefix.length).replace(/^\/+/, '');
  return env.ASSETS.fetch(new Request(url.toString(), req));
}
