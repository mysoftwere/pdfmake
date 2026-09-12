/**
 * =============================================================================
 *   VIRAL PDF MAKER - CLIENT-SIDE GITHUB PAGES READY ENGINE
 * =============================================================================
 */

// Global State
let currentImageDataUrl = "";
let isDefaultImage = true;
let generatedPdfs = []; // { filename, blob, url, title }

// DOM Elements
const targetUrlInput = document.getElementById("targetUrl");
const titleFileInput = document.getElementById("titleFileInput");
const titleUploadZone = document.getElementById("titleUploadZone");
const titlesTextarea = document.getElementById("titlesTextarea");
const titleCountBadge = document.getElementById("titleCount");

const imageFileInput = document.getElementById("imageFileInput");
const imageUploadZone = document.getElementById("imageUploadZone");
const imagePreview = document.getElementById("imagePreview");
const imageStatusText = document.getElementById("imageStatusText");
const btnResetImage = document.getElementById("btnResetImage");

const tomorrowPreview = document.getElementById("tomorrowPreview");
const customDateInput = document.getElementById("customDateInput");
const labelDateTomorrow = document.getElementById("labelDateTomorrow");
const labelDateCustom = document.getElementById("labelDateCustom");
const radioDateChoices = document.querySelectorAll('input[name="dateChoice"]');

const bodyTemplate = document.getElementById("bodyTemplate");
const customKeyword = document.getElementById("customKeyword");

const btnGenerate = document.getElementById("btnGenerate");
const progressBox = document.getElementById("progressBox");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");

const resultsCard = document.getElementById("resultsCard");
const successCountSpan = document.getElementById("successCount");
const pdfList = document.getElementById("pdfList");
const btnDownloadZip = document.getElementById("btnDownloadZip");

const customPrefixInput = document.getElementById("customPrefixInput");
const startSerialInput = document.getElementById("startSerialInput");
const filenamePreviewText = document.getElementById("filenamePreviewText");

// =============================================================================
//  1. DATE FORMATTING & INITIALIZATION
// =============================================================================
function formatDocDate(dateObj) {
  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  const month = months[dateObj.getMonth()];
  const day = dateObj.getDate();
  const year = dateObj.getFullYear();
  return `[LAST UPDATED: ${month} ${day < 10 ? '0' + day : day}, ${year}]`;
}

function getTomorrowDate() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d;
}

function initDates() {
  const tomorrow = getTomorrowDate();
  tomorrowPreview.textContent = formatDocDate(tomorrow);

  // Set default custom date to tomorrow's ISO string (YYYY-MM-DD)
  const yyyy = tomorrow.getFullYear();
  const mm = String(tomorrow.getMonth() + 1).padStart(2, '0');
  const dd = String(tomorrow.getDate()).padStart(2, '0');
  customDateInput.value = `${yyyy}-${mm}-${dd}`;

  radioDateChoices.forEach(radio => {
    radio.addEventListener("change", (e) => {
      if (e.target.value === "tomorrow") {
        labelDateTomorrow.classList.add("active");
        labelDateCustom.classList.remove("active");
        customDateInput.disabled = true;
      } else {
        labelDateCustom.classList.add("active");
        labelDateTomorrow.classList.remove("active");
        customDateInput.disabled = false;
        customDateInput.focus();
      }
    });
  });
}

function getSelectedDateString() {
  const selected = document.querySelector('input[name="dateChoice"]:checked').value;
  if (selected === "tomorrow") {
    return formatDocDate(getTomorrowDate());
  } else {
    const val = customDateInput.value;
    if (!val) return formatDocDate(getTomorrowDate());
    const [y, m, d] = val.split("-");
    const chosen = new Date(parseInt(y, 10), parseInt(m, 10) - 1, parseInt(d, 10));
    return formatDocDate(chosen);
  }
}

// =============================================================================
//  2. DEFAULT IMAGE GENERATION (Canvas Banner)
// =============================================================================
function createDefaultBannerDataUrl() {
  const canvas = document.createElement("canvas");
  canvas.width = 680;
  canvas.height = 360;
  const ctx = canvas.getContext("2d");

  // Modern gradient background
  const grad = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
  grad.addColorStop(0, "#0f172a");
  grad.addColorStop(1, "#1e293b");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Decorative border
  ctx.strokeStyle = "#f43f5e";
  ctx.lineWidth = 6;
  ctx.strokeRect(12, 12, canvas.width - 24, canvas.height - 24);

  // Play icon circle
  ctx.fillStyle = "#f43f5e";
  ctx.beginPath();
  ctx.arc(canvas.width / 2, 135, 45, 0, Math.PI * 2);
  ctx.fill();

  // Play triangle
  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  ctx.moveTo(canvas.width / 2 - 12, 115);
  ctx.lineTo(canvas.width / 2 + 18, 135);
  ctx.lineTo(canvas.width / 2 - 12, 155);
  ctx.closePath();
  ctx.fill();

  // Banner text
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 28px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("CLICK HERE TO WATCH FULL VIDEO", canvas.width / 2, 235);

  ctx.fillStyle = "#94a3b8";
  ctx.font = "bold 16px sans-serif";
  ctx.fillText("High Definition • Official Access • Instant Play", canvas.width / 2, 275);

  return canvas.toDataURL("image/jpeg", 0.9);
}

function setDefaultImage() {
  if (typeof FIXED_DEFAULT_BANNER_DATA_URL !== "undefined" && FIXED_DEFAULT_BANNER_DATA_URL) {
    currentImageDataUrl = FIXED_DEFAULT_BANNER_DATA_URL;
  } else {
    currentImageDataUrl = createDefaultBannerDataUrl();
  }
  isDefaultImage = true;
  imagePreview.src = currentImageDataUrl;
  imageStatusText.textContent = "ফিক্সড ব্যানার সক্রিয় (Screenshot 2026-09-09 092247.jpg)";
  imageFileInput.value = "";
}

// =============================================================================
//  3. FILE UPLOADS (.txt and Images)
// =============================================================================
function updateTitleCount() {
  const lines = titlesTextarea.value
    .split("\n")
    .map(t => t.trim())
    .filter(t => t.length > 0);
  titleCountBadge.textContent = `${lines.length} টি টাইটেল`;
}

function initUploadHandlers() {
  const titleUploadSuccess = document.getElementById("titleUploadSuccess");

  // Title File Upload (.txt)
  titleUploadZone.addEventListener("click", () => titleFileInput.click());
  
  titleFileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target.result;
      titlesTextarea.value = text;
      updateTitleCount();
      updateFilenamePreview();
      if (titleUploadSuccess) {
        const lines = text.split("\n").map(t => t.trim()).filter(t => t.length > 0);
        titleUploadSuccess.textContent = `✅ "${file.name}" ফাইল সফলভাবে লোড হয়েছে! মোট ${lines.length} টি টাইটেল পাওয়া গেছে।`;
        titleUploadSuccess.classList.remove("hidden");
      }
    };
    reader.readAsText(file);
  });

  titlesTextarea.addEventListener("input", () => {
    updateTitleCount();
    updateFilenamePreview();
  });

  // Image Upload
  imageUploadZone.addEventListener("click", () => imageFileInput.click());

  imageFileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      currentImageDataUrl = event.target.result;
      isDefaultImage = false;
      imagePreview.src = currentImageDataUrl;
      imageStatusText.textContent = `কাস্টম ছবি: ${file.name.substring(0, 18)}...`;
    };
    reader.readAsDataURL(file);
  });

  btnResetImage.addEventListener("click", setDefaultImage);

  // Filename & Serial Listeners
  if (customPrefixInput) customPrefixInput.addEventListener("input", updateFilenamePreview);
  if (startSerialInput) startSerialInput.addEventListener("input", updateFilenamePreview);
}

// =============================================================================
//  FILENAME & SLUG FORMATTING (e.g. viral-video-sexy-1.pdf)
// =============================================================================
function formatTitleSlug(rawTitle) {
  if (!rawTitle) return "viral-video";
  let slug = rawTitle
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  if (slug.length > 35) {
    slug = slug.substring(0, 35).replace(/-+$/, "");
  }
  return slug || "viral-video";
}

function updateFilenamePreview() {
  if (!filenamePreviewText) return;
  const prefix = customPrefixInput ? customPrefixInput.value.trim() : "";
  const startNum = parseInt(startSerialInput ? startSerialInput.value : 1, 10) || 1;
  const firstTitle = titlesTextarea.value.split("\n").map(t => t.trim()).find(t => t.length > 0) || "viral video sexy";
  const base = prefix ? formatTitleSlug(prefix) : formatTitleSlug(firstTitle);
  filenamePreviewText.textContent = `${base}-${startNum}.pdf, ${base}-${startNum + 1}.pdf, ${base}-${startNum + 2}.pdf...`;
}

// =============================================================================
//  4. PDF GENERATION ENGINE (jsPDF Client-Side)
// =============================================================================
async function generateSinglePdf(title, targetUrl, dateStr, templateText, keyword, serialIndex = 1, customPrefix = "") {
  const { jsPDF } = window.jspdf;
  // A4 size: 595.28 x 841.89 pt
  const doc = new jsPDF({
    unit: "pt",
    format: "a4",
    orientation: "portrait"
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 50; // ~18mm margin
  const contentWidth = pageWidth - (margin * 2);

  // 1. Prepare Text Replacements
  let activeKeyword = keyword || title.split(" ").slice(0, 4).join(" ");
  const randomNum = String(Math.floor(Math.random() * 59) + 1).padStart(2, '0');

  let processedBody = templateText
    .replace(/Titleesss/g, title)
    .replace(/keywordss/g, activeKeyword)
    .replace(/numberss/g, randomNum);

  // Split into before and after image
  let textBeforeImage = "";
  let textAfterImage = "";
  if (processedBody.includes("Imagesvsd")) {
    const parts = processedBody.split("Imagesvsd");
    textBeforeImage = parts[0].trim();
    textAfterImage = parts[1] ? parts[1].trim() : "";
  } else {
    textBeforeImage = processedBody.trim();
  }

  let curY = margin + 20;

  // 2. Render Document Title (22pt Bold, Centered)
  doc.setFont("helvetica", "bold");
  doc.setFontSize(22);
  doc.setTextColor(17, 24, 39); // Dark grey #111827

  const titleLines = doc.splitTextToSize(title, contentWidth);
  doc.text(titleLines, pageWidth / 2, curY, { align: "center" });
  curY += (titleLines.length * 28) + 14;

  // 3. Render Red Date (12pt Bold, Centered)
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.setTextColor(217, 4, 41); // Red #d90429
  doc.text(dateStr, pageWidth / 2, curY, { align: "center" });
  curY += 28;

  // 4. Render Banner Image with Clickable Hyperlink (Enlarged to full content width)
  const imgWidth = Math.min(520, contentWidth);
  const imgHeight = (imgWidth / 16) * 9.5; // Slightly larger ratio
  const imgX = margin + (contentWidth - imgWidth) / 2;

  try {
    doc.addImage(currentImageDataUrl, "JPEG", imgX, curY, imgWidth, imgHeight);
    
    // ⭐ Add Clickable Web Link on the Image
    if (targetUrl) {
      doc.link(imgX, curY, imgWidth, imgHeight, { url: targetUrl });
    }
  } catch (err) {
    console.warn("Could not embed image, drawing placeholder box:", err);
    doc.setDrawColor(200, 200, 200);
    doc.rect(imgX, curY, imgWidth, imgHeight);
    if (targetUrl) {
      doc.link(imgX, curY, imgWidth, imgHeight, { url: targetUrl });
    }
  }

  // Set Document Title in PDF Metadata so browser tabs/headers display the exact title!
  doc.setProperties({
    title: title,
    subject: title,
    author: "PDF Generator"
  });

  // 7. Generate output blob — filename = slug-serial (e.g. tamil-sex-video-7.pdf)
  const pdfBlob = doc.output("blob");
  let fileBase = "";
  if (customPrefix && customPrefix.trim()) {
    fileBase = formatTitleSlug(customPrefix.trim());
  } else {
    const rawSlug = formatTitleSlug(title);
    fileBase = rawSlug.length > 35 ? rawSlug.substring(0, 35).replace(/-+$/, "") : rawSlug;
  }
  const filename = `${fileBase || "viral-video"}-${serialIndex}.pdf`;

  return {
    filename,
    blob: pdfBlob,
    url: URL.createObjectURL(pdfBlob),
    title
  };
}

// =============================================================================
//  5. BATCH GENERATION WORKFLOW
// =============================================================================
async function startGeneration() {
  const rawTitles = titlesTextarea.value
    .split("\n")
    .map(t => t.trim())
    .filter(t => t.length > 0);

  if (rawTitles.length === 0) {
    alert("অনুগ্রহ করে অন্তত ১টি Title লিখুন বা .txt ফাইল সিলেক্ট করুন!");
    titlesTextarea.focus();
    return;
  }

  let targetUrl = targetUrlInput.value.trim();
  if (!targetUrl) {
    // Fixed default link (hidden from UI)
    targetUrl = "https://leakhdrvideo.blogspot.com/2026/06/pdf.html";
  }

  const dateStr = getSelectedDateString();
  const template = bodyTemplate ? bodyTemplate.value : "";
  const kw = customKeyword ? customKeyword.value.trim() : "";

  // Reset UI for progress
  btnGenerate.disabled = true;
  progressBox.classList.remove("hidden");
  resultsCard.classList.add("hidden");
  pdfList.innerHTML = "";
  generatedPdfs = [];

  const total = rawTitles.length;
  progressFill.style.width = "0%";
  progressText.textContent = `শুরু হচ্ছে... মোট ${total} টি ফাইল তৈরি হবে`;

  const startSerial = parseInt(startSerialInput ? startSerialInput.value : 1, 10) || 1;
  const prefix = customPrefixInput ? customPrefixInput.value.trim() : "";

  for (let i = 0; i < total; i++) {
    const title = rawTitles[i];
    const currentSerial = startSerial + i;
    progressText.textContent = `প্রসেসিং (${i + 1}/${total}): ${title.substring(0, 30)}...`;
    
    // Allow UI to breathe
    await new Promise(r => setTimeout(r, 40));

    try {
      const pdfItem = await generateSinglePdf(title, targetUrl, dateStr, template, kw, currentSerial, prefix);
      generatedPdfs.push(pdfItem);
      addPdfResultItem(pdfItem);
    } catch (err) {
      console.error("PDF generation failed for:", title, err);
    }

    const pct = Math.round(((i + 1) / total) * 100);
    progressFill.style.width = `${pct}%`;
  }

  // Done
  progressText.textContent = `🎉 সম্পন্ন হয়েছে! মোট ${generatedPdfs.length} টি PDF প্রস্তুত।`;
  btnGenerate.disabled = false;
  successCountSpan.textContent = generatedPdfs.length;
  resultsCard.classList.remove("hidden");
  resultsCard.scrollIntoView({ behavior: "smooth" });
}

function addPdfResultItem(pdfItem) {
  const itemDiv = document.createElement("div");
  itemDiv.className = "pdf-item";

  itemDiv.innerHTML = `
    <span class="pdf-item-title" title="${pdfItem.title}">
      📄 ${pdfItem.filename} (${pdfItem.title})
    </span>
    <a href="${pdfItem.url}" download="${pdfItem.filename}" class="btn-download-single">
      ⬇️ ডাউনলোড
    </a>
  `;
  pdfList.appendChild(itemDiv);
}

// =============================================================================
//  6. ZIP DOWNLOAD (JSZip)
// =============================================================================
async function downloadAllAsZip() {
  if (generatedPdfs.length === 0) return;

  btnDownloadZip.disabled = true;
  btnDownloadZip.textContent = "⏳ ZIP ফাইল তৈরি হচ্ছে...";

  try {
    const zip = new JSZip();
    generatedPdfs.forEach(item => {
      zip.file(item.filename, item.blob);
    });

    const zipBlob = await zip.generateAsync({ type: "blob" });
    const dateStr = new Date().toISOString().slice(0, 10);
    saveAs(zipBlob, `Viral_PDFs_${dateStr}.zip`);
  } catch (err) {
    console.error("ZIP creation failed:", err);
    alert("ZIP ডাউনলোড করতে সমস্যা হয়েছে। দয়া করে প্রতিটি ফাইল আলাদাভাবে ডাউনলোড করুন।");
  } finally {
    btnDownloadZip.disabled = false;
    btnDownloadZip.textContent = "📦 সব ফাইল এক ক্লিকে ZIP ডাউনলোড করুন";
  }
}

// =============================================================================
//  7. EVENT LISTENERS & BOOTSTRAP
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initDates();
  setDefaultImage();
  initUploadHandlers();

  // Automatically load titles from Titel/titel.txt if available
  fetch("Titel/titel.txt")
    .then(r => r.ok ? r.text() : "")
    .then(text => {
      if (text.trim() && !titlesTextarea.value.trim()) {
        titlesTextarea.value = text.trim();
        updateTitleCount();
        updateFilenamePreview();
        const successBadge = document.getElementById("titleUploadSuccess");
        if (successBadge) {
          const count = text.trim().split("\n").filter(l => l.trim()).length;
          successBadge.textContent = `✅ 'Titel/titel.txt' ফাইল থেকে ${count} টি টাইটেল স্বয়ংক্রিয়ভাবে লোড হয়েছে!`;
          successBadge.classList.remove("hidden");
        }
      }
    })
    .catch(() => {});

  updateFilenamePreview();
  titlesTextarea.addEventListener("input", updateFilenamePreview);

  btnGenerate.addEventListener("click", startGeneration);
  btnDownloadZip.addEventListener("click", downloadAllAsZip);
});
