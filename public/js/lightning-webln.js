const LIGHTNING_ADDRESS = 'emin@nuri.com';

document.addEventListener('DOMContentLoaded', function() {
    initializeLightning();
});

async function initializeLightning() {
    const status = document.getElementById('webln-status');
    if (status && typeof window.webln !== 'undefined') {
        status.textContent = 'Alby detected';
    }
    
    document.querySelectorAll('.tip-btn').forEach(button => {
        button.addEventListener('click', handleTipClick);
    });
}

async function handleTipClick(event) {
    const amount = parseInt(event.target.dataset.amount);
    
    if (typeof window.webln !== 'undefined') {
        try {
            await window.webln.enable();
            const [username, domain] = LIGHTNING_ADDRESS.split('@');
            const lnurlResponse = await fetch(`https://${domain}/.well-known/lnurlp/${username}`);
            
            if (lnurlResponse.ok) {
                const lnurlData = await lnurlResponse.json();
                const invoiceResponse = await fetch(`${lnurlData.callback}?amount=${amount * 1000}`);
                const invoiceData = await invoiceResponse.json();
                
                if (invoiceData.pr) {
                    const result = await window.webln.sendPayment(invoiceData.pr);
                    showSuccess(amount);
                    return;
                }
            }
        } catch (error) {
            console.log('WebLN payment failed:', error);
        }
    }
    
    fallbackPayment(amount);
}

function fallbackPayment(amount) {
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.95); display: flex; align-items: center; justify-content: center; z-index: 9999;';
    
    modal.innerHTML = `
        <div style="text-align: center; padding: 40px; max-width: 400px;">
            <p style="font-size: 24px; margin: 0 0 20px 0;">${amount} sats</p>
            <p style="font-family: monospace; font-size: 18px; margin: 0 0 30px 0; padding: 20px; background: #f5f5f5;">${LIGHTNING_ADDRESS}</p>
            
            <div style="display: flex; gap: 12px; justify-content: center;">
                <button onclick="window.open('lightning:${LIGHTNING_ADDRESS}?amount=${amount}', '_self')" style="padding: 10px 20px; background: #f7931a; color: white; border: none; font-size: 14px; cursor: pointer;">Open Wallet</button>
                <button onclick="navigator.clipboard.writeText('${LIGHTNING_ADDRESS}')" style="padding: 10px 20px; background: transparent; color: #000; border: 1px solid #000; font-size: 14px; cursor: pointer;">Copy Address</button>
                <button onclick="this.closest('div').parentElement.remove()" style="padding: 10px 20px; background: transparent; color: #666; border: 1px solid #666; font-size: 14px; cursor: pointer;">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function showSuccess(amount) {
    const notification = document.createElement('div');
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #000; color: white; padding: 16px 24px; font-size: 14px; z-index: 10000;';
    notification.textContent = `Sent ${amount} sats. Thank you!`;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}
