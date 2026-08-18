/**
 * net-sub Pages Functions 中间件
 * 只有 /sub/<SECRET>/... 路径才能访问 dist/ 产物
 * SECRET 通过环境变量 SUB_PATH_SECRET 注入
 */
export async function onRequest(context) {
  const { request, next, env } = context;
  const url = new URL(request.url);
  const secret = env.SUB_PATH_SECRET;
  if (!secret) {
    return new Response('Server misconfiguration: SUB_PATH_SECRET not set', { status: 500 });
  }
  // 必须以 /sub/<secret>/ 开头
  const prefix = `/sub/${secret}/`;
  if (!url.pathname.startsWith(prefix)) {
    // 无 secret 或 secret 错误 → 404（不泄露路径结构）
    return new Response('Not Found', { status: 404 });
  }
  // 去掉 /sub/<secret>/ 前缀，继续走静态文件或下一个 handler
  url.pathname = url.pathname.slice(prefix.length);
  const newRequest = new Request(url.toString(), request);
  return next(newRequest);
}
