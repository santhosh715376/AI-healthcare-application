import React from 'react';

export default function ChatBubble({ role, content }) {
  if (role === 'user') {
    return (
      <div className="chat-message-row user">
        <div className="chat-user-pill">
          {content}
        </div>
      </div>
    );
  }

  // Multi-block content parser: handles mixed paragraphs, markdown tables, and numbered lists seamlessly
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
      // Check for numbered list item
      else if (/^\d+\.\s/.test(trimmed)) {
        if (currentBlock && currentBlock.type === 'ol') {
          currentBlock.items.push(trimmed.replace(/^\d+\.\s/, ''));
        } else {
          currentBlock = { type: 'ol', items: [trimmed.replace(/^\d+\.\s/, '')] };
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
      <div className="chat-ai-content">
        {blocks.map((block, bIdx) => {
          if (block.type === 'table' && block.lines.length >= 2) {
            const headers = block.lines[0].split('|').map(s => s.trim()).filter(Boolean);
            const rows = block.lines.slice(2).map(row => row.split('|').map(s => s.trim()).filter(Boolean));

            return (
              <div key={bIdx} className="chat-table-wrapper">
                <table className="chat-rendered-table">
                  <thead>
                    <tr>
                      {headers.map((h, hIdx) => <th key={hIdx}>{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, rIdx) => (
                      <tr key={rIdx}>
                        {r.map((c, cIdx) => <td key={cIdx}>{c}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          }

          if (block.type === 'ol') {
            return (
              <ol key={bIdx} className="chat-rendered-ol">
                {block.items.map((item, iIdx) => (
                  <li key={iIdx}>{item}</li>
                ))}
              </ol>
            );
          }

          return (
            <p key={bIdx} style={{ marginBottom: '8px' }}>
              {block.lines.join(' ')}
            </p>
          );
        })}
      </div>
    );
  };

  return (
    <div className="chat-message-row assistant">
      <div className="chat-reasoning-tag">
        Devised straightforward explanation for query
      </div>
      {renderAiContent(content)}
    </div>
  );
}
