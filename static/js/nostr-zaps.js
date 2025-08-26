// Nostr and Lightning Zaps Integration
const LIGHTNING_ADDRESS = "emino@emino.app";

async function sendZap(amount) {
    // Check for WebLN (Alby extension)
    if (typeof window.webln !== 'undefined') {
        try {
            await window.webln.enable();
            const invoice = await fetchInvoice(amount);
            if (invoice) {
                await window.webln.sendPayment(invoice);
                showSuccess(amount);
                return;
            }
        } catch (e) {
            console.log("WebLN payment failed, trying other methods");
        }
    }
    
    // Fallback to Lightning URL
    const lnurl = `lightning:${LIGHTNING_ADDRESS}?amount=${amount}`;
    window.open(lnurl, '_blank');
}

async function fetchInvoice(amount) {
    try {
        const response = await fetch(`/.well-known/lnurlp/emino`);
        const data = await response.json();
        
        if (data.callback) {
            const invoiceResponse = await fetch(`${data.callback}?amount=${amount * 1000}`);
            const invoiceData = await invoiceResponse.json();
            return invoiceData.pr;
        }
    } catch (error) {
        console.error("Failed to fetch invoice:", error);
    }
    return null;
}

function showSuccess(amount) {
    alert(`⚡ Thank you for the ${amount} sats tip!`);
}

window.sendZap = sendZap;
