import React, { useState, useCallback } from 'react';

export default function AuditTrail({ auditChain }) {
    const [verifying, setVerifying] = useState(false);
    const [verified, setVerified] = useState(false);
    const [verifyIndex, setVerifyIndex] = useState(-1);

    const lastThree = auditChain.slice(-3);

    const handleVerify = useCallback(() => {
        if (verifying) return;
        setVerifying(true);
        setVerified(false);

        let i = 0;
        const interval = setInterval(() => {
            setVerifyIndex(i);
            i++;
            if (i >= lastThree.length) {
                clearInterval(interval);
                setTimeout(() => {
                    setVerifyIndex(-1);
                    setVerifying(false);
                    setVerified(true);
                    setTimeout(() => setVerified(false), 3000);
                }, 300);
            }
        }, 200);
    }, [verifying, lastThree.length]);

    return (
        <div className="panel" style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 12, padding: '8px 12px' }}>
            <div className="section-title" style={{ marginBottom: 0, whiteSpace: 'nowrap' }}>AUDIT CHAIN</div>
            <div className="audit-entries">
                {lastThree.map((entry, i) => (
                    <React.Fragment key={entry.blockNumber}>
                        <div className={`audit-block ${verifying && verifyIndex === i ? 'verifying' : ''}`}>
                            <div className="audit-block-number">#{String(entry.blockNumber).padStart(4, '0')}</div>
                            <div className="audit-block-agent">{entry.agent}</div>
                            <div className="audit-block-decision">{entry.decision}</div>
                            <div className="audit-block-hash">{entry.hash}</div>
                        </div>
                        {i < lastThree.length - 1 && <span className="audit-arrow">→</span>}
                    </React.Fragment>
                ))}
                <button
                    className={`verify-btn ${verified ? 'verified' : ''}`}
                    onClick={handleVerify}
                    disabled={verifying}
                >
                    {verifying ? 'VERIFYING...' : verified ? '✓ CHAIN VERIFIED' : 'VERIFY CHAIN'}
                </button>
            </div>
        </div>
    );
}
