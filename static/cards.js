// Card Display Extension
// This file adds SVG card rendering and overlapping card layout

// Create SVG card element with improved layout
function createCardSVG(card) {
    if (card.type === 'char') {
        // 文字カード: 左上に大きくひらがな
        return `
            <svg viewBox="0 0 120 168" xmlns="http://www.w3.org/2000/svg">
                <text x="15" y="40" text-anchor="start" 
                      font-family="'M PLUS Rounded 1c', sans-serif" 
                      font-size="36" font-weight="800" fill="#2c3e50">
                    ${card.display}
                </text>
            </svg>
        `;
    } else if (card.type === 'row') {
        // 行カード: 左上に先頭文字大きく、下に小さく縦並び
        const chars = card.value.split('');
        const firstChar = chars[0];
        const restChars = chars.slice(1);

        return `
            <svg viewBox="0 0 120 168" xmlns="http://www.w3.org/2000/svg">
                <text x="15" y="35" text-anchor="start" 
                      font-family="'M PLUS Rounded 1c', sans-serif" 
                      font-size="32" font-weight="800" fill="#2c3e50">
                    ${firstChar}
                </text>
                ${restChars.map((char, i) => `
                    <text x="15" y="${55 + i * 18}" text-anchor="start" 
                          font-family="'M PLUS Rounded 1c', sans-serif" 
                          font-size="14" font-weight="600" fill="#555">
                        ${char}
                    </text>
                `).join('')}
            </svg>
        `;
    } else if (card.type === 'length') {
        // 文字数カード: 数字を左上に (7は7+と表記)
        const displayNum = card.value === '7' ? '7+' : card.value;
        return `
            <svg viewBox="0 0 120 168" xmlns="http://www.w3.org/2000/svg">
                <text x="15" y="40" text-anchor="start" 
                      font-family="'M PLUS Rounded 1c', sans-serif" 
                      font-size="36" font-weight="800" fill="#2c3e50">
                    ${displayNum}
                </text>
            </svg>
        `;
    }
}

// Override renderHand function with centered overlapping card layout
const originalRenderHand = renderHand;
renderHand = function () {
    els.hand.innerHTML = '';

    const totalCards = state.hand.length;
    if (totalCards === 0) return;

    // Detect mobile
    const isMobile = window.innerWidth <= 768;
    const overlap = isMobile ? 40 : 60; // Comfortable overlap on mobile
    const cardWidth = isMobile ? 80 : 120; // Smaller cards on mobile

    // Calculate center offset - properly center the card group
    const totalWidth = (totalCards - 1) * overlap + cardWidth;
    const centerOffset = -totalWidth / 2;

    state.hand.forEach((card, index) => {
        const cardEl = document.createElement('div');
        cardEl.className = 'card';
        cardEl.dataset.index = index; // Store index for hover effects

        const isSelected = index === state.selectedCardIndex;
        const isAutoSelected = cardEl.classList.contains('auto-selected');

        if (isSelected) {
            cardEl.classList.add('selected');
        }

        // Position cards with overlap and separation when selected or auto-selected
        let offset = centerOffset + index * overlap;

        // Find auto-selected card index
        let autoSelectedIndex = -1;
        if (!isSelected && state.autoSelect && els.wordInput?.value) {
            // Check if this card is auto-selected by checking the current hand
            state.hand.forEach((c, i) => {
                if (i === index && cardEl.classList.contains('auto-selected')) {
                    autoSelectedIndex = i;
                }
            });
        }

        // If a card is selected or auto-selected, push cards to the left and right
        const shiftAmount = isMobile ? 20 : 30; // Smaller shift on mobile
        const activeIndex = state.selectedCardIndex !== -1 ? state.selectedCardIndex : autoSelectedIndex;

        if (activeIndex !== -1) {
            if (index < activeIndex) {
                offset -= shiftAmount;
            } else if (index > activeIndex) {
                offset += shiftAmount;
            }
        }

        cardEl.style.left = `calc(50% + ${offset}px)`;
        cardEl.style.zIndex = (isSelected || isAutoSelected) ? 102 : index + 1;

        // Use SVG for card content
        cardEl.innerHTML = createCardSVG(card);

        // Hover effect - separate cards (only on non-mobile)
        if (!isMobile) {
            cardEl.addEventListener('mouseenter', (e) => {
                if (state.selectedCardIndex === -1) {
                    const hoverIndex = parseInt(e.currentTarget.dataset.index);
                    updateCardPositionsOnHover(hoverIndex);
                }
            });

            cardEl.addEventListener('mouseleave', () => {
                if (state.selectedCardIndex === -1) {
                    updateCardPositionsOnHover(null);
                }
            });
        }

        cardEl.addEventListener('click', () => selectCard(index));
        els.hand.appendChild(cardEl);
    });

    // Re-apply auto-select highlight if input has text
    if (state.autoSelect && els.wordInput.value) {
        highlightAutoSelectedCard(els.wordInput.value);
    }
};

// Update card positions based on hover
function updateCardPositionsOnHover(hoverIndex) {
    const cards = els.hand.querySelectorAll('.card');
    const totalCards = cards.length;
    const overlap = 60;
    const cardWidth = 120;
    const totalWidth = (totalCards - 1) * overlap + cardWidth;
    const centerOffset = -totalWidth / 2;

    cards.forEach((cardEl, index) => {
        let offset = centerOffset + index * overlap;

        if (hoverIndex !== null) {
            if (index < hoverIndex) {
                offset -= 30;
            } else if (index > hoverIndex) {
                offset += 30;
            }
        }

        cardEl.style.left = `calc(50% + ${offset}px)`;

        // Update z-index for hover
        if (index === hoverIndex) {
            cardEl.style.zIndex = 101;
        } else {
            cardEl.style.zIndex = index + 1;
        }
    });
}

console.log("Card SVG and overlapping layout loaded");
