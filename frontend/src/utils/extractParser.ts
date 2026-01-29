export function extractTextParts(html: string) {
  const doc = new DOMParser().parseFromString(html, "text/html");

  const root = doc.body;
  if (!root) return [];

  const walker = doc.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const text = node.nodeValue?.trim();
      if (!text) return NodeFilter.FILTER_REJECT;

      const el = (node as Text).parentElement;
      if (!el) return NodeFilter.FILTER_REJECT;

      if (el.closest("nav,header,footer,aside,[role='navigation']"))
        return NodeFilter.FILTER_REJECT;

      return NodeFilter.FILTER_ACCEPT;
    },
  });

    // 1) collect text node references
    const nodes: Text[] = [];
    let n: Node | null;
    while ((n = walker.nextNode())) nodes.push(n as Text);
  
    // 2) send texts to NLP (placeholder)
    for (const node of nodes) {
      const original = node.nodeValue ?? "";
      const wrapped = original; // TODO: replace with NLP result
  
      if (wrapped === original) continue;
  
      const template = doc.createElement("template");
      template.innerHTML = wrapped;
      node.replaceWith(template.content);
    }
}
// DEMO: insert <wbr> between Thai characters (very naive)
function demoWrapThai(text: string): string {
  // only touch Thai-ish lines; keep other text unchanged
  if (/[ก-๙]/.test(text)) return `<wbr>${text}`;
  return text;
}

export function wrapThaiInHtmlDemo(html: string): string {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const root = doc.querySelector("main") ?? doc.body;
  if (!root) return html;

  const walker = doc.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const raw = node.nodeValue ?? "";
      if (!raw.trim()) return NodeFilter.FILTER_REJECT;

      const el = (node as Text).parentElement;
      if (!el) return NodeFilter.FILTER_REJECT;

      // skip non-content areas
      if (el.closest("nav,header,footer,aside,[role='navigation'],script,style,noscript,code,pre"))
        return NodeFilter.FILTER_REJECT;

      return NodeFilter.FILTER_ACCEPT;
    },
  });

  const textNodes: Text[] = [];
  let n: Node | null;
  while ((n = walker.nextNode())) textNodes.push(n as Text);

  for (const node of textNodes) {
    const original = node.nodeValue ?? "";
    const wrappedHtml = demoWrapThai(original);

    if (wrappedHtml === original) continue;

    const template = doc.createElement("template");
    template.innerHTML = wrappedHtml;
    node.replaceWith(template.content); // replaces at the exact same spot
  }

  const doctype = doc.doctype ? `<!DOCTYPE ${doc.doctype.name}>` : "";
  return doctype + "\n" + doc.documentElement.outerHTML;
}

// const root = $0;

// const walker = document.createTreeWalker(
//   root,
//   NodeFilter.SHOW_ELEMENT,
//   {
//     acceptNode(node) {
//       return node instanceof HTMLSpanElement
//         ? NodeFilter.FILTER_ACCEPT
//         : NodeFilter.FILTER_SKIP;
//     }
//   }
// );

// let node;
// while ((node = walker.nextNode())) {
//   console.log(node);
// }


// export async function extractTextParts (html: string) {
//     const doc = new DOMParser().parseFromString(html, "text/html");
//      // ✅ scan main content first, fallback to body
//     const root = (doc.querySelector("main") as HTMLElement) ?? doc.body;
//     if (!root) return [];

//   // remove junk
//     doc.querySelectorAll("script,style,noscript").forEach(n => n.remove());

//     const walker = doc.createTreeWalker(
//       root,
//       NodeFilter.SHOW_TEXT,
//       {
//         acceptNode(node) {
//           const t = node.nodeValue ?? "";
//           if (!t.trim()) return NodeFilter.FILTER_REJECT;

//           const p = (node as Text).parentElement;
//           if (!p) return NodeFilter.FILTER_REJECT;

//           // ✅ exclude nav-like areas
//           if (p.closest("nav,header,footer,aside")) return NodeFilter.FILTER_REJECT;
//           if (p.closest('[role="navigation"]')) return NodeFilter.FILTER_REJECT;

//           return NodeFilter.FILTER_ACCEPT;
//         },
//       }
//     );

//   const parts: string[] = [];
//   let n: Node | null;
//   while ((n = walker.nextNode())) parts.push((n.nodeValue ?? "").trim());

//   return parts;
// };

