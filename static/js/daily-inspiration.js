/* BUILDSPOT_DAILY_INSPIRATION_PREMIUM_POSTER */
(function () {
  "use strict";

  const data = document.getElementById("bsDailyPosterData");
  const modal = document.getElementById("bsDailyModal");
  const closeButton = document.getElementById("bsDailyClose");
  const canvas = document.getElementById("bsDailyPosterPreview");
  if (!data) return;

  const date = data.dataset.date || new Date().toISOString().slice(0, 10);
  const quote = data.dataset.quote || "";
  const theme = data.dataset.theme || "";
  const displayDate = data.dataset.displayDate || date;
  const imageUrl = data.dataset.image || "";
  const logoUrl = data.dataset.logo || "";

  const shareMessage =
    quote + "\n\n" +
    theme + "\n\n" +
    "Planning a building project? Find trusted suppliers and compare building materials.\n" +
    "Explore stores across Nigeria on BuildSpot.\n\n" +
    "Visit https://buildspot.store and build with confidence!";

  function storageGet(key) {
    try { return localStorage.getItem(key); }
    catch (e) {
      try { return sessionStorage.getItem(key); } catch (e2) { return null; }
    }
  }
  function storageSet(key, value) {
    try { localStorage.setItem(key, value); }
    catch (e) {
      try { sessionStorage.setItem(key, value); } catch (e2) {}
    }
  }

  // Mark as seen as soon as it is displayed, not only when it is closed.
  if (modal) {
    const seenKey = "buildspot_daily_inspiration_seen_" + date;
    if (storageGet(seenKey) !== "1") {
      storageSet(seenKey, "1");
      modal.classList.add("bs-daily-modal-visible");
      modal.setAttribute("aria-hidden", "false");
    }
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.remove("bs-daily-modal-visible");
    modal.setAttribute("aria-hidden", "true");
  }
  if (closeButton) closeButton.addEventListener("click", closeModal);
  if (modal) {
    modal.addEventListener("click", function (event) {
      if (event.target === modal) closeModal();
    });
  }
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeModal();
  });

  function loadImage(url) {
    return new Promise(function (resolve, reject) {
      if (!url) return reject(new Error("Image URL is missing"));
      const img = new Image();
      img.onload = function () { resolve(img); };
      img.onerror = function () { reject(new Error("Could not load poster image")); };
      img.src = url;
    });
  }

  function roundedRect(ctx, x, y, w, h, r) {
    const radius = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.arcTo(x + w, y, x + w, y + h, radius);
    ctx.arcTo(x + w, y + h, x, y + h, radius);
    ctx.arcTo(x, y + h, x, y, radius);
    ctx.arcTo(x, y, x + w, y, radius);
    ctx.closePath();
  }

  function wrapText(ctx, text, x, y, maxWidth, lineHeight, maxLines) {
    const words = String(text).split(/\s+/);
    let line = "";
    let lines = 0;
    for (let i = 0; i < words.length; i++) {
      const test = line ? line + " " + words[i] : words[i];
      if (ctx.measureText(test).width > maxWidth && line) {
        ctx.fillText(line, x, y);
        y += lineHeight;
        lines++;
        line = words[i];
        if (lines >= maxLines - 1) break;
      } else {
        line = test;
      }
    }
    const remaining = words.slice(words.indexOf(line.split(" ")[0]) + line.split(" ").length);
    if (lines < maxLines) {
      if (remaining.length) line += "…";
      ctx.fillText(line, x, y);
      lines++;
    }
    return y + lineHeight;
  }

  let posterBlobPromise;
  async function makePosterBlob() {
    if (posterBlobPromise) return posterBlobPromise;
    posterBlobPromise = (async function () {
      const poster = document.createElement("canvas");
      // HD export: 2160 x 3840 pixels, with the original design coordinates.
      poster.width = 2160;
      poster.height = 3840;
      const ctx = poster.getContext("2d");
      ctx.scale(2, 2);

      let background;
      try { background = await loadImage(imageUrl); } catch (e) { background = null; }
      if (background) {
        const scale = Math.max(1080 / background.width, 1920 / background.height);
        const sw = background.width * scale;
        const sh = background.height * scale;
        ctx.drawImage(background, (1080 - sw) / 2, (1920 - sh) / 2, sw, sh);
      } else {
        const gradient = ctx.createLinearGradient(0, 0, 1080, 1920);
        gradient.addColorStop(0, "#5a3324");
        gradient.addColorStop(1, "#1f1713");
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 1080, 1920);
      }

      ctx.fillStyle = "rgba(20, 13, 10, .76)";
      ctx.fillRect(0, 0, 1080, 1920);

      ctx.strokeStyle = "#e66b37";
      ctx.lineWidth = 8;
      roundedRect(ctx, 42, 42, 996, 1836, 34);
      ctx.stroke();

      // Logo panel with the real BuildSpot logo.
      ctx.fillStyle = "#fffaf4";
      roundedRect(ctx, 110, 112, 860, 245, 28);
      ctx.fill();
      try {
        const logo = await loadImage(logoUrl);
        const maxLogo = 205;
        const ratio = Math.min(maxLogo / logo.width, maxLogo / logo.height);
        const lw = logo.width * ratio;
        const lh = logo.height * ratio;
        ctx.drawImage(logo, 145, 132, lw, lh);
      } catch (e) {
        ctx.fillStyle = "#c6532b";
        ctx.font = "bold 58px Arial";
        ctx.fillText("BUILDSPOT", 150, 255);
      }

      ctx.fillStyle = "#33231b";
      ctx.font = "bold 58px Arial";
      ctx.fillText("BUILDSPOT", 390, 225);
      ctx.font = "bold 23px Arial";
      ctx.fillStyle = "#9b5335";
      ctx.fillText("BUILD BETTER. SOURCE SMARTER.", 393, 270);

      ctx.textAlign = "center";
      ctx.fillStyle = "#f6a06e";
      ctx.font = "bold 34px Arial";
      ctx.fillText("DAILY INSPIRATION", 540, 500);
      ctx.fillStyle = "#fff4e9";
      ctx.font = "bold 27px Arial";
      ctx.fillText(displayDate.toUpperCase(), 540, 560);

      ctx.fillStyle = "#e66b37";
      roundedRect(ctx, 495, 625, 90, 8, 4);
      ctx.fill();

      ctx.fillStyle = "#ffffff";
      ctx.textAlign = "center";
      ctx.font = "bold 54px Arial";
      const words = quote.split(/\s+/);
      let lines = [];
      let line = "";
      const maxWidth = 820;
      words.forEach(function (word) {
        const test = line ? line + " " + word : word;
        if (ctx.measureText(test).width > maxWidth && line) {
          lines.push(line);
          line = word;
        } else {
          line = test;
        }
      });
      if (line) lines.push(line);

      const maxLines = 8;
      if (lines.length > maxLines) {
        lines = lines.slice(0, maxLines);
        lines[maxLines - 1] = lines[maxLines - 1].replace(/[.,;:]?$/, "…");
      }
      const lineHeight = 76;
      const totalHeight = lines.length * lineHeight;
      let y = Math.max(790, 1050 - totalHeight / 2);
      lines.forEach(function (text) {
        ctx.fillText(text, 540, y, maxWidth);
        y += lineHeight;
      });

      ctx.fillStyle = "#f6a06e";
      ctx.font = "bold 34px Arial";
      ctx.fillText(theme.toUpperCase(), 540, Math.min(y + 95, 1510), 850);

      ctx.fillStyle = "#fff4e9";
      ctx.font = "bold 38px Arial";
      ctx.fillText("BUILD SOMETHING GREAT.", 540, 1660);
      ctx.font = "26px Arial";
      ctx.fillStyle = "#e9d7ca";
      ctx.fillText("Discover suppliers. Build with confidence.", 540, 1715);
      ctx.fillStyle = "#f6a06e";
      ctx.font = "bold 31px Arial";
      ctx.fillText("www.buildspot.store", 540, 1810);

      return new Promise(function (resolve, reject) {
        poster.toBlob(function (blob) {
          if (blob) resolve(blob);
          else reject(new Error("Could not create poster image"));
        }, "image/png");
      });
    })();
    return posterBlobPromise;
  }

  function filename() {
    return "BuildSpot-Daily-Inspiration-" + date + ".png";
  }
  async function downloadPoster() {
    const blob = await makePosterBlob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename();
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 30000);
  }

  document.querySelectorAll("[data-bs-daily-download]").forEach(function (button) {
    button.addEventListener("click", function () {
      downloadPoster().catch(function () {
        alert("Sorry, the poster could not be created. Please reload the page and try again.");
      });
    });
  });

  // Copy the full caption so it can be pasted into WhatsApp Status.
  function legacyCopyCaption() {
    const field = document.createElement("textarea");
    field.value = shareMessage;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.left = "-9999px";
    document.body.appendChild(field);
    field.select();

    let copied = false;
    try {
      copied = document.execCommand("copy");
    } catch (error) {
      copied = false;
    }

    field.remove();
    return copied;
  }

  function copyDailyCaption() {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(shareMessage)
        .then(function () { return true; })
        .catch(function () { return legacyCopyCaption(); });
    }
    return Promise.resolve(legacyCopyCaption());
  }

  document.querySelectorAll("[data-bs-daily-share-image]").forEach(function (button) {
    button.addEventListener("click", async function () {
      // Start clipboard copying directly from the user's click.
      const captionPromise = copyDailyCaption();

      try {
        const blob = await makePosterBlob();
        const file = new File([blob], filename(), { type: "image/png" });

        if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
          await navigator.share({
            files: [file],
            title: "BuildSpot Daily Inspiration",
            text: shareMessage,
            url: "https://buildspot.store"
          });

          const copied = await captionPromise;

          if (copied) {
            alert("Your poster has been shared and your complete caption has been copied. In WhatsApp Status, tap the caption field and choose Paste to add the daily quote and BuildSpot website link.");
          } else {
            alert("Your poster has been shared. Clipboard copying was blocked by the browser. Please use the WhatsApp text-sharing option for the full caption.");
          }
        } else {
          await downloadPoster();
          const copied = await captionPromise;

          if (copied) {
            alert("Your HD poster is downloaded and your complete caption is copied. Open WhatsApp Status, select the poster, tap the caption field and choose Paste.");
          } else {
            alert("Your HD poster is downloaded. Open WhatsApp Status and upload it. Clipboard copying was unavailable in this browser.");
          }
        }
      } catch (error) {
        if (error && error.name === "AbortError") return;

        // If sharing fails, the downloaded image and copied caption remain useful.
        try {
          await downloadPoster();
        } catch (downloadError) {}

        const copied = await captionPromise;
        alert(copied
          ? "The poster was downloaded and the caption copied. Upload the poster to WhatsApp Status and paste the caption."
          : "Image sharing failed. Please use Download image and try again.");
      }
    });
  });

  // WhatsApp text sharing always includes the daily quote and website invitation.
  document.querySelectorAll("[data-bs-daily-share]").forEach(function (link) {
    link.href = "https://wa.me/?text=" + encodeURIComponent(shareMessage);
    link.target = "_blank";
    link.rel = "noopener";
  });

  if (canvas) {
    makePosterBlob().then(function (blob) {
      const url = URL.createObjectURL(blob);
      const preview = new Image();
      preview.onload = function () {
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(preview, 0, 0, canvas.width, canvas.height);
        URL.revokeObjectURL(url);
      };
      preview.src = url;
    }).catch(function (error) {
      console.warn("BuildSpot poster preview:", error);
    });
  }
})();
