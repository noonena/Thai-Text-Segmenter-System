// function collectTextNodes(root: HTMLElement) {
//     const walker = root.ownerDocument!.createTreeWalker(
//       root,
//       NodeFilter.SHOW_TEXT,
//       {
//         acceptNode(node) {
//           const text = node.nodeValue ?? "";
//           if (!text.trim()) return NodeFilter.FILTER_REJECT;
  
//           const parent = (node as Text).parentElement;
//           if (!parent) return NodeFilter.FILTER_REJECT;
  
//           if (parent.closest("script,style,noscript,code,pre")) return NodeFilter.FILTER_REJECT;
//           return NodeFilter.FILTER_ACCEPT;
//         },
//       }
//     );

//     const nodes: Text[] = [];
//     let n: Node | null;
//     while ((n = walker.nextNode())) nodes.push(n as Text);
//     return nodes;
//   }
  
//   // TEMP: replace this with your real Thai word segmentation output
//   async function wrapThaiText(text: string): Promise<string> {
//     // Example placeholder: do nothing
//     return text;
  
//     // Later: call your Python API here and return something like:
//     // "ประเทศ<wbr>ไทย<wbr>..."
//   }
  
//   export async function wrapThaiInHtml(html: string): Promise<string> {
//     const doc = new DOMParser().parseFromString(html, "text/html");
  
//     const body = doc.body;
//     if (!body) return html;
  
//     // optional: remove junk
//     doc.querySelectorAll("script, style, noscript").forEach((n) => n.remove());
  
//     const textNodes = collectTextNodes(body);
  
//     for (const node of textNodes) {
//       const original = node.nodeValue ?? "";
//       const wrappedHtml = await wrapThaiText(original);
  
//       if (wrappedHtml === original) continue;
  
//       // Replace text node with HTML (wbr/spans)
//       const template = doc.createElement("template");
//       template.innerHTML = wrappedHtml;
//       node.parentNode?.replaceChild(template.content, node);
//     }
  
//     const doctype = doc.doctype ? `<!DOCTYPE ${doc.doctype.name}>` : "";
//     return doctype + "\n" + doc.documentElement.outerHTML;
//   }
  