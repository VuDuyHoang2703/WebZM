export default async function handler(req, res) {
  const { url } = req.query;

  if (!url || !url.startsWith('https://oss.zmrobo.com/')) {
    return res.status(400).json({ error: 'Chỉ hỗ trợ stream video từ nguồn oss.zmrobo.com' });
  }

  const range = req.headers.range;
  const upstreamHeaders = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://oss.zmrobo.com/'
  };
  if (range) {
    upstreamHeaders['Range'] = range;
  }

  try {
    const upstreamRes = await fetch(url, { headers: upstreamHeaders });

    res.status(upstreamRes.status);

    const forwardHeaders = ['content-type', 'content-length', 'content-range', 'accept-ranges', 'last-modified', 'etag'];
    for (const [key, val] of upstreamRes.headers.entries()) {
      if (forwardHeaders.includes(key.toLowerCase())) {
        res.setHeader(key, val);
      }
    }

    // Edge cache tối ưu: Lưu cache tại Vercel Edge Singapore 1 năm để người xem tại Việt Nam tải tức thì 0.1s
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Cache-Control', 'public, s-maxage=31536000, max-age=86400, stale-while-revalidate=86400');

    if (!upstreamRes.body) {
      return res.end();
    }

    const reader = upstreamRes.body.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(value);
    }
    return res.end();
  } catch (error) {
    console.error('Vercel Edge Video Stream Error:', error);
    return res.status(502).json({ error: 'Lỗi kết nối máy chủ CDN: ' + error.message });
  }
}

