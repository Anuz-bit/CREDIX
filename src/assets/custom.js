
// Wait for DOM to load fully
document.addEventListener('DOMContentLoaded', () => {
    // Function to run the animation on a single element
    const animateElement = (el) => {
        // Prevent re-animation or interfering with completed ones
        if (el.dataset.animating === 'true') return;

        const finalValueStr = el.getAttribute('data-value');
        if (!finalValueStr) return;

        // Mark as animating
        el.dataset.animating = 'true';

        // Detect type from string
        const isCurrency = finalValueStr.includes('₹');
        const isPercent = finalValueStr.includes('%');

        // Remove non-numeric chars except for . and -
        // If it's a "₹20,00,000", parseFloat works poorly with commas sometimes depending on locale, 
        // so best to strip commas first.
        const cleanValStr = finalValueStr.replace(/,/g, '').replace(/[^\d.-]/g, '');
        const cleanVal = parseFloat(cleanValStr);

        if (isNaN(cleanVal)) {
            // If parsing fails, just show the text immediately
            el.innerText = finalValueStr;
            return;
        }

        let startTimestamp = null;
        const duration = 2000; // 2 seconds

        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);

            // Ease-out cubic function: 1 - (1 - t)^3
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentVal = (easeOut * cleanVal);

            let displayVal;
            if (isCurrency) {
                // Format with Indian locale for currency
                displayVal = '₹' + Math.floor(currentVal).toLocaleString('en-IN');
            } else if (isPercent) {
                // Keep 1 decimal for percentage
                displayVal = currentVal.toFixed(1) + '%';
            } else {
                // Standard integer format
                displayVal = Math.floor(currentVal).toLocaleString('en-IN');
            }

            el.innerText = displayVal;

            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                // Ensure final value matches exactly what was passed
                el.innerText = finalValueStr;
                el.classList.add('animation-complete');
            }
        };
        window.requestAnimationFrame(step);
    };

    // Observer to watch for new elements added to the DOM (Dash dynamic updates)
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                // If it's an element node
                if (node.nodeType === 1) {
                    // Case 1: The added node IS the target
                    if (node.classList.contains('kpi-value-animate')) {
                        animateElement(node);
                    }
                    // Case 2: The added node contains targets
                    // Queries subtree for any new matching elements
                    else if (node.querySelectorAll) {
                        const targets = node.querySelectorAll('.kpi-value-animate');
                        targets.forEach(animateElement);
                    }
                }
            });
        });
    });

    // Start observing the body for child list changes and subtree
    observer.observe(document.body, { childList: true, subtree: true });

    // Initial check for elements already present (in case script runs late)
    const initialElements = document.querySelectorAll('.kpi-value-animate');
    initialElements.forEach(animateElement);
});
