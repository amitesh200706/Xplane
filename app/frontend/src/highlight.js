// Minimal single-line tokenizer for the code viewer.
// Returns an array of { text, cls } tokens; cls maps to .tok-* classes in index.css.

const TOKEN_RE =
  /(#.*$|\/\/.*$)|("[^"]*"|'[^']*'|`[^`]*`)|(@[A-Za-z_]\w*)|\b(def|class|import|from|return|if|elif|else|for|while|in|not|and|or|is|with|as|try|except|finally|raise|pass|break|continue|lambda|yield|global|nonlocal|async|await|None|True|False|self|new|function|const|let|var)\b|\b(\d+(?:\.\d+)?)\b|([A-Za-z_]\w*)(?=\s*\()/g;

export function tokenizeLine(line) {
  if (!line) return [];
  const tokens = [];
  let last = 0;
  let m;
  TOKEN_RE.lastIndex = 0;

  const push = (text, cls) => {
    if (text) tokens.push(cls ? { text, cls } : { text });
  };

  while ((m = TOKEN_RE.exec(line)) !== null) {
    push(line.slice(last, m.index));
    if (m[1]) push(m[1], 'tok-com');
    else if (m[2]) push(m[2], 'tok-str');
    else if (m[3]) push(m[3], 'tok-dec');
    else if (m[4]) push(m[4], 'tok-kw');
    else if (m[5]) push(m[5], 'tok-num');
    else if (m[6]) push(m[6], 'tok-fn');
    last = TOKEN_RE.lastIndex;
  }
  push(line.slice(last));

  return tokens;
}
