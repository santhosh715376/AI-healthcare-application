import React from 'react';

export default function ChatBubble({ role, content }) {
  if (role === 'user') {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
        <div style={{
          backgroundColor: '#2f2f2f',
          color: '#ffffff',
          padding: '10px 18px',
          borderRadius: '20px',
          maxWidth: '75%',
          fontSize: '0.95rem',
          lineHeight: '1.5',
          wordBreak: 'break-word'
        }}>
          {content}
        </div>
      </div>
    );
  }

  // Parse inline markdown formatting (**bold**, *italic*, code)
  const formatText = (str) => {
    if (!str) return '';
    // Replace **bold** with <strong>
    const parts = str.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={idx} style={{ color: '#ffffff', fontWeight: 600 }}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return <em key={idx} style={{ color: '#d4d4d4' }}>{part.slice(1, -1)}</em>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={idx} style={{ backgroundColor: '#171717', color: '#60a5fa', padding: '2px 6px', borderRadius: '4px', fontSize: '0.85rem' }}>{part.slice(1, -1)}</code>;
      }
      return part;
    });
  };

  const renderAiContent = (text) => {
    if (!text) return null;

    const lines = text.split('\n');
    const blocks = [];
    let currentBlock = null;

    lines.forEach((line) => {
      const trimmed = line.trim();

      if (!trimmed) {
        if (currentBlock && currentBlock.type === 'p') {
          currentBlock = null;
        }
        return;
      }

      // Check for markdown table line
      if (trimmed.startsWith('|')) {
        if (currentBlock && currentBlock.type === 'table') {
          currentBlock.lines.push(trimmed);
        } else {
          currentBlock = { type: 'table', lines: [trimmed] };
          blocks.push(currentBlock);
        }
      }
      // Check for bullet list item
      else if (trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
        const itemText = trimmed.replace(/^[-•]\s+/, '');
        if (currentBlock && currentBlock.type === 'ul') {
          currentBlock.items.push(itemText);
        } else {
          currentBlock = { type: 'ul', items: [itemText] };
          blocks.push(currentBlock);
        }
      }
      // Check for numbered list item
      else if (/^\d+\.\s/.test(trimmed)) {
        const itemText = trimmed.replace(/^\d+\.\s/, '');
        if (currentBlock && currentBlock.type === 'ol') {
          currentBlock.items.push(itemText);
        } else {
          currentBlock = { type: 'ol', items: [itemText] };
          blocks.push(currentBlock);
        }
      }
      // Default paragraph
      else {
        if (currentBlock && currentBlock.type === 'p') {
          currentBlock.lines.push(trimmed);
        } else {
          currentBlock = { type: 'p', lines: [trimmed] };
          blocks.push(currentBlock);
        }
      }
    });

    return (
      <div style={{ color: '#ececec', fontSize: '0.95rem', lineHeight: '1.6' }}>
        {blocks.map((block, bIdx) => {
          if (block.type === 'table' && block.lines.length >= 2) {
            const headers = block.lines[0].split('|').map(s => s.trim()).filter(Boolean);
            const rows = block.lines.slice(2).map(row => row.split('|').map(s => s.trim()).filter(Boolean));

            return (
              <div key={bIdx} style={{ overflowX: 'auto', margin: '12px 0' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: '#171717', border: '1px solid #262626', borderRadius: '8px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#262626' }}>
                      {headers.map((h, hIdx) => (
                        <th key={hIdx} style={{ padding: '8px 12px', textAlign: 'left', fontSize: '0.85rem', fontWeight: 600, color: '#38bdf8' }}>
                          {formatText(h)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, rIdx) => (
                      <tr key={rIdx} style={{ borderTop: '1px solid #262626' }}>
                        {r.map((c, cIdx) => (
                          <td key={cIdx} style={{ padding: '8px 12px', fontSize: '0.85rem' }}>
                            {formatText(c)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          }

          if (block.type === 'ul') {
            return (
              <ul key={bIdx} style={{ margin: '8px 0', paddingLeft: '20px' }}>
                {block.items.map((item, iIdx) => (
                  <li key={iIdx} style={{ marginBottom: '4px' }}>{formatText(item)}</li>
                ))}
              </ul>
            );
          }

          if (block.type === 'ol') {
            return (
              <ol key={bIdx} style={{ margin: '8px 0', paddingLeft: '20px' }}>
                {block.items.map((item, iIdx) => (
                  <li key={iIdx} style={{ marginBottom: '4px' }}>{formatText(item)}</li>
                ))}
              </ol>
            );
          }

          return (
            <p key={bIdx} style={{ marginBottom: '8px', marginTop: 0 }}>
              {formatText(block.lines.join(' '))}
            </p>
          );
        })}
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start', marginBottom: '16px' }}>
      {/* ChatGPT Assistant Avatar Icon */}
      <div style={{
        width: '30px',
        height: '30px',
        borderRadius: '50%',
        backgroundColor: '#10b981',
        color: '#ffffff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 700,
        fontSize: '0.85rem',
        flexShrink: 0
      }}>
        🤖
      </div>
      <div style={{ flex: 1 }}>
        {renderAiContent(content)}
      </div>
    </div>
  );
}
