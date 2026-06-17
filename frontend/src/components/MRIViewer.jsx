import React, { useRef, useEffect, useState } from 'react';

const colormaps = {
  jet: (v) => {
    const points = [
      { t: 0.0, c: [0, 0, 127] },
      { t: 0.15, c: [0, 0, 255] },
      { t: 0.35, c: [0, 255, 255] },
      { t: 0.55, c: [0, 255, 0] },
      { t: 0.75, c: [255, 255, 0] },
      { t: 0.9, c: [255, 0, 0] },
      { t: 1.0, c: [127, 0, 0] }
    ];
    return interpolateColormap(v, points);
  },
  hot: (v) => {
    const points = [
      { t: 0.0, c: [0, 0, 0] },
      { t: 0.3, c: [180, 0, 0] },
      { t: 0.6, c: [255, 127, 0] },
      { t: 0.85, c: [255, 255, 0] },
      { t: 1.0, c: [255, 255, 255] }
    ];
    return interpolateColormap(v, points);
  },
  viridis: (v) => {
    const points = [
      { t: 0.0, c: [68, 1, 84] },
      { t: 0.25, c: [59, 82, 139] },
      { t: 0.5, c: [33, 144, 141] },
      { t: 0.75, c: [94, 201, 98] },
      { t: 1.0, c: [253, 231, 37] }
    ];
    return interpolateColormap(v, points);
  },
  plasma: (v) => {
    const points = [
      { t: 0.0, c: [13, 8, 135] },
      { t: 0.25, c: [126, 3, 168] },
      { t: 0.5, c: [204, 71, 120] },
      { t: 0.75, c: [248, 149, 64] },
      { t: 1.0, c: [240, 249, 33] }
    ];
    return interpolateColormap(v, points);
  }
};

function interpolateColormap(v, points) {
  if (v <= points[0].t) return points[0].c;
  if (v >= points[points.length - 1].t) return points[points.length - 1].c;
  for (let i = 0; i < points.length - 1; i++) {
    const p1 = points[i];
    const p2 = points[i + 1];
    if (v >= p1.t && v <= p2.t) {
      const ratio = (v - p1.t) / (p2.t - p1.t);
      return [
        Math.floor(p1.c[0] + ratio * (p2.c[0] - p1.c[0])),
        Math.floor(p1.c[1] + ratio * (p2.c[1] - p1.c[1])),
        Math.floor(p1.c[2] + ratio * (p2.c[2] - p1.c[2]))
      ];
    }
  }
  return [0, 0, 0];
}

const MRIViewer = ({ imageUrl, attentionMap, opacity, colormap = 'jet' }) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [image, setImage] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Load Image when imageUrl changes
  useEffect(() => {
    if (!imageUrl) return;
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      setImage(img);
      setZoom(1);
      setPan({ x: 0, y: 0 });
    };
    img.src = imageUrl;
  }, [imageUrl]);

  // Redraw Canvas when dependencies change
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !image) return;
    const ctx = canvas.getContext('2d');

    // Clean canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    // Apply pan and zoom
    ctx.translate(canvas.width / 2 + pan.x, canvas.height / 2 + pan.y);
    ctx.scale(zoom, zoom);
    ctx.translate(-canvas.width / 2, -canvas.height / 2);

    // Draw Original MRI Scan
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

    // Render & Blend Attention Overlay
    if (attentionMap && attentionMap.length > 0 && opacity > 0) {
      // 1. Render 14x14 attention map onto offscreen canvas
      const H = attentionMap.length;
      const W = attentionMap[0].length;
      const offscreen = document.createElement('canvas');
      offscreen.width = W;
      offscreen.height = H;
      const offCtx = offscreen.getContext('2d');
      const imgData = offCtx.createImageData(W, H);

      const colorFn = colormaps[colormap] || colormaps.jet;

      for (let y = 0; y < H; y++) {
        for (let x = 0; x < W; x++) {
          const val = attentionMap[y][x];
          const rgb = colorFn(val);
          const idx = (y * W + x) * 4;
          imgData.data[idx] = rgb[0];     // R
          imgData.data[idx + 1] = rgb[1]; // G
          imgData.data[idx + 2] = rgb[2]; // B
          imgData.data[idx + 3] = 255;    // A (fully opaque offscreen, transparency applied at blend stage)
        }
      }
      offCtx.putImageData(imgData, 0, 0);

      // 2. Draw offscreen 14x14 onto main canvas using scaling and smoothing (bilinear interpolation)
      ctx.globalAlpha = opacity;
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(offscreen, 0, 0, canvas.width, canvas.height);
      ctx.globalAlpha = 1.0;
    }

    ctx.restore();
  }, [image, attentionMap, opacity, colormap, zoom, pan]);

  // Handle Dragging / Panning
  const handleMouseDown = (e) => {
    if (!image) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Handle Scroll to Zoom
  const handleWheel = (e) => {
    if (!image) return;
    e.preventDefault();
    const zoomFactor = 1.1;
    let nextZoom = zoom;
    if (e.deltaY < 0) {
      nextZoom = Math.min(zoom * zoomFactor, 6);
    } else {
      nextZoom = Math.max(zoom / zoomFactor, 0.8);
    }
    setZoom(nextZoom);
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className="mri-viewer-wrapper" ref={containerRef} onWheel={handleWheel}>
      <div className="viewer-toolbar">
        <span className="toolbar-title">Interactive Neuro Scan</span>
        <div className="toolbar-actions">
          <button className="btn-secondary btn-xs" onClick={() => setZoom(z => Math.min(z * 1.2, 6))}>Zoom In</button>
          <button className="btn-secondary btn-xs" onClick={() => setZoom(z => Math.max(z / 1.2, 0.8))}>Zoom Out</button>
          <button className="btn-secondary btn-xs" onClick={resetView}>Reset View</button>
        </div>
      </div>
      <div
        className="canvas-container"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
      >
        {image ? (
          <canvas
            ref={canvasRef}
            width={448}
            height={448}
            className="mri-canvas"
          />
        ) : (
          <div className="viewer-placeholder">
            <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
            </svg>
            <p>Upload a patient MRI scan to begin neural attention mapping</p>
          </div>
        )}
      </div>
      <div className="viewer-footer">
        <span className="footer-tip">💡 Tip: Use mouse wheel to Zoom, Drag to Pan around the scan.</span>
        {zoom !== 1 && <span className="zoom-indicator">Scale: {Math.round(zoom * 100)}%</span>}
      </div>
    </div>
  );
};

export default MRIViewer;
