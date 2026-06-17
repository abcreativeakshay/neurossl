export default {
  async fetch(request, env, ctx) {
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${env.APP_TITLE}</title>
  <meta name="description" content="${env.APP_DESCRIPTION}">
  
  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="${env.APP_TITLE}">
  <meta property="og:description" content="${env.APP_DESCRIPTION}">
  <meta property="og:image" content="https://huggingface.co/spaces/ABCREATIVEAKSHAY/neuro-ssl/resolve/main/data/figures/confusion_matrix.png">

  <!-- Twitter -->
  <meta property="twitter:card" content="summary_large_image">
  <meta property="twitter:title" content="${env.APP_TITLE}">
  <meta property="twitter:description" content="${env.APP_DESCRIPTION}">

  <!-- Fonts & Styles -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
  
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    
    html, body {
      width: 100%;
      height: 100%;
      overflow: hidden;
      background-color: #f8fafc;
      font-family: 'Outfit', sans-serif;
    }

    /* Seamless Iframe Container */
    .app-container {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      border: none;
      z-index: 1;
      opacity: 0;
      transition: opacity 0.8s ease-in-out;
    }

    /* Premium Light Loader Styling */
    .loader-wrapper {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: radial-gradient(ellipse at 50% 40%, rgba(5, 150, 105, 0.06) 0%, #f8fafc 60%);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 10;
      transition: opacity 0.5s ease-out, visibility 0.5s ease-out;
    }

    .brain-icon {
      font-size: 80px;
      margin-bottom: 24px;
      animation: pulse 2.5s infinite ease-in-out;
      filter: drop-shadow(0 0 20px rgba(5, 150, 105, 0.25));
    }

    h1 {
      font-size: 32px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 8px;
      background: linear-gradient(135deg, #0f172a 30%, #059669 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    p {
      color: #64748b;
      font-size: 15px;
      font-weight: 400;
      margin-bottom: 32px;
      text-align: center;
    }

    .progress-bar-bg {
      width: 240px;
      height: 5px;
      background-color: rgba(0, 0, 0, 0.06);
      border-radius: 999px;
      overflow: hidden;
      position: relative;
    }

    .progress-bar-fill {
      width: 0%;
      height: 100%;
      background: linear-gradient(90deg, #059669, #10b981, #d97706);
      border-radius: 999px;
      box-shadow: 0 0 10px rgba(5, 150, 105, 0.35);
      animation: progress 2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
    }

    @keyframes pulse {
      0%, 100% {
        transform: scale(1);
        filter: drop-shadow(0 0 15px rgba(5, 150, 105, 0.2));
      }
      50% {
        transform: scale(1.08);
        filter: drop-shadow(0 0 30px rgba(5, 150, 105, 0.4));
      }
    }

    @keyframes progress {
      0% { width: 0%; }
      50% { width: 70%; }
      100% { width: 100%; }
    }
  </style>
</head>
<body>

  <!-- Fullscreen Iframe embedding the Hugging Face Space Embed URL -->
  <iframe 
    id="app-iframe" 
    class="app-container" 
    src="${env.SPACE_EMBED_URL}?v=3" 
    allow="accelerometer; autoplay; camera; gyroscope; magnetometer; microphone; serial; usb"
  ></iframe>

  <!-- Beautiful Light Splash Loader -->
  <div id="loader" class="loader-wrapper">
    <div class="brain-icon">🧠</div>
    <h1>NeuroSSL</h1>
    <p>Connecting to Edge Diagnostics...</p>
    <div class="progress-bar-bg">
      <div class="progress-bar-fill"></div>
    </div>
  </div>

  <script>
    const iframe = document.getElementById('app-iframe');
    const loader = document.getElementById('loader');

    // Smooth transition once the iframe finishes loading
    iframe.onload = function() {
      setTimeout(() => {
        loader.style.opacity = '0';
        loader.style.visibility = 'hidden';
        iframe.style.opacity = '1';
      }, 300);
    };
  </script>
</body>
</html>
    `;

    return new Response(html, {
      headers: {
        "content-type": "text/html;charset=UTF-8",
        "cache-control": "public, max-age=60",
      },
    });
  },
};
