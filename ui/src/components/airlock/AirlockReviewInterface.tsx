import React, { useState, useEffect } from 'react';
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Eye,
  FileText,
  Image,
  Video
} from 'lucide-react';

interface Asset {
  id: string;
  title: string;
  type: string;
  status: string;
  content_url?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface ValidationReport {
  compliance_score: number;
  violations: Array<{
    rule_id: string;
    rule_name: string;
    severity: string;
    description: string;
    recommendation: string;
  }>;
  recommendations: string[];
}

const AirlockReviewInterface: React.FC = () => {
  const [pendingAssets, setPendingAssets] = useState<Asset[]>([]);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [asset, setAsset] = useState<Asset | null>(null);
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);
  const [activeTab, setActiveTab] = useState<'content' | 'validation' | 'review'>('content');
  const [currentComment, setCurrentComment] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchPendingAssets();
  }, []);

  useEffect(() => {
    if (selectedAssetId) {
      fetchAssetDetails(selectedAssetId);
      fetchValidationReport(selectedAssetId);
    }
  }, [selectedAssetId]);

  const fetchPendingAssets = async () => {
    try {
      const response = await fetch('http://localhost:8007/assets/pending');
      const data = await response.json();
      setPendingAssets(data);
    } catch (error) {
      console.error('Failed to fetch pending assets:', error);
    }
  };

  const fetchAssetDetails = async (assetId: string) => {
    try {
      const response = await fetch(`http://localhost:8007/assets/${assetId}`);
      const data = await response.json();
      setAsset(data);
    } catch (error) {
      console.error('Failed to fetch asset details:', error);
    }
  };

  const fetchValidationReport = async (assetId: string) => {
    try {
      const response = await fetch('http://localhost:8005/validate-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action_type: 'publish_content',
          entity_type: 'creative_asset',
          entity_id: assetId,
          metadata: {}
        })
      });
      const data = await response.json();
      setValidationReport({
        compliance_score: data.compliance_score,
        violations: data.violations || [],
        recommendations: data.recommendations || []
      });
    } catch (error) {
      console.error('Failed to fetch validation report:', error);
    }
  };

  const handleApprove = async () => {
    if (!selectedAssetId) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8007/approve/${selectedAssetId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer_id: 'current-user',
          comments: currentComment,
          metadata: {}
        })
      });
      
      if (response.ok) {
        alert('Asset approved successfully!');
        fetchPendingAssets();
        setSelectedAssetId(null);
        setAsset(null);
        setCurrentComment('');
      }
    } catch (error) {
      console.error('Failed to approve asset:', error);
      alert('Failed to approve asset');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedAssetId || !rejectionReason.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8007/reject/${selectedAssetId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer_id: 'current-user',
          reason: rejectionReason,
          comments: currentComment,
          metadata: {}
        })
      });
      
      if (response.ok) {
        alert('Asset rejected successfully!');
        fetchPendingAssets();
        setSelectedAssetId(null);
        setAsset(null);
        setCurrentComment('');
        setRejectionReason('');
      }
    } catch (error) {
      console.error('Failed to reject asset:', error);
      alert('Failed to reject asset');
    } finally {
      setIsLoading(false);
    }
  };

  const getAssetIcon = (type: string) => {
    switch (type) {
      case 'image': return <Image style={{ width: '16px', height: '16px' }} />;
      case 'video': return <Video style={{ width: '16px', height: '16px' }} />;
      case 'document': return <FileText style={{ width: '16px', height: '16px' }} />;
      default: return <FileText style={{ width: '16px', height: '16px' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending_review': return { backgroundColor: '#fef3c7', color: '#92400e' };
      case 'approved': return { backgroundColor: '#d1fae5', color: '#065f46' };
      case 'rejected': return { backgroundColor: '#fee2e2', color: '#991b1b' };
      default: return { backgroundColor: '#f3f4f6', color: '#374151' };
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return { backgroundColor: '#fee2e2', color: '#991b1b' };
      case 'medium': return { backgroundColor: '#fed7aa', color: '#9a3412' };
      case 'low': return { backgroundColor: '#fef3c7', color: '#92400e' };
      default: return { backgroundColor: '#f3f4f6', color: '#374151' };
    }
  };

  if (pendingAssets.length === 0) {
    return (
      <div style={{ width: '100%', backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px 24px' }}>
          <CheckCircle style={{ width: '48px', height: '48px', color: '#10b981', marginBottom: '16px' }} />
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>No Pending Reviews</h3>
          <p style={{ color: '#6b7280', textAlign: 'center' }}>
            All content has been reviewed. New submissions will appear here for approval.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
      <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' }}>
        <div style={{ padding: '24px', borderBottom: '1px solid #e5e7eb' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock style={{ width: '20px', height: '20px' }} />
            Pending Reviews ({pendingAssets.length})
          </h2>
        </div>
        <div style={{ padding: '24px' }}>
          {pendingAssets.map((pendingAsset) => (
            <div
              key={pendingAsset.id}
              style={{
                padding: '12px',
                borderRadius: '8px',
                border: selectedAssetId === pendingAsset.id ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                backgroundColor: selectedAssetId === pendingAsset.id ? '#eff6ff' : 'white',
                cursor: 'pointer',
                marginBottom: '8px'
              }}
              onClick={() => setSelectedAssetId(pendingAsset.id)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                {getAssetIcon(pendingAsset.type)}
                <span style={{ fontWeight: '500', fontSize: '14px' }}>{pendingAsset.title}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ 
                  padding: '2px 8px', 
                  fontSize: '12px', 
                  borderRadius: '9999px',
                  ...getStatusColor(pendingAsset.status)
                }}>
                  {pendingAsset.status.replace('_', ' ')}
                </span>
                <span style={{ fontSize: '12px', color: '#6b7280' }}>
                  {new Date(pendingAsset.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' }}>
        {asset ? (
          <div>
            <div style={{ padding: '24px', borderBottom: '1px solid #e5e7eb' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h2 style={{ fontSize: '18px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {getAssetIcon(asset.type)}
                  {asset.title}
                </h2>
                <span style={{ 
                  padding: '2px 8px', 
                  fontSize: '12px', 
                  borderRadius: '9999px',
                  ...getStatusColor(asset.status)
                }}>
                  {asset.status.replace('_', ' ')}
                </span>
              </div>
            </div>

            <div style={{ padding: '24px' }}>
              <div style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb' }}>
                  <button
                    style={{
                      padding: '8px 16px',
                      fontWeight: '500',
                      borderBottom: activeTab === 'content' ? '2px solid #3b82f6' : 'none',
                      color: activeTab === 'content' ? '#3b82f6' : '#6b7280',
                      backgroundColor: 'transparent',
                      border: 'none',
                      cursor: 'pointer'
                    }}
                    onClick={() => setActiveTab('content')}
                  >
                    Content
                  </button>
                  <button
                    style={{
                      padding: '8px 16px',
                      fontWeight: '500',
                      borderBottom: activeTab === 'validation' ? '2px solid #3b82f6' : 'none',
                      color: activeTab === 'validation' ? '#3b82f6' : '#6b7280',
                      backgroundColor: 'transparent',
                      border: 'none',
                      cursor: 'pointer'
                    }}
                    onClick={() => setActiveTab('validation')}
                  >
                    Validation
                  </button>
                  <button
                    style={{
                      padding: '8px 16px',
                      fontWeight: '500',
                      borderBottom: activeTab === 'review' ? '2px solid #3b82f6' : 'none',
                      color: activeTab === 'review' ? '#3b82f6' : '#6b7280',
                      backgroundColor: 'transparent',
                      border: 'none',
                      cursor: 'pointer'
                    }}
                    onClick={() => setActiveTab('review')}
                  >
                    Review
                  </button>
                </div>
              </div>

              {activeTab === 'content' && (
                <div>
                  <div style={{ backgroundColor: '#f9fafb', padding: '16px', borderRadius: '8px', marginBottom: '16px' }}>
                    <h4 style={{ fontWeight: '500', marginBottom: '8px' }}>Asset Details</h4>
                    <div style={{ fontSize: '14px' }}>
                      <div style={{ marginBottom: '4px' }}><strong>Type:</strong> {asset.type}</div>
                      <div style={{ marginBottom: '4px' }}><strong>Created:</strong> {new Date(asset.created_at).toLocaleString()}</div>
                      <div style={{ marginBottom: '4px' }}><strong>Updated:</strong> {new Date(asset.updated_at).toLocaleString()}</div>
                      {asset.content_url && (
                        <div>
                          <strong>Content URL:</strong>
                          <a href={asset.content_url} target="_blank" rel="noopener noreferrer" style={{ color: '#3b82f6', textDecoration: 'underline', marginLeft: '4px' }}>
                            View Content
                          </a>
                        </div>
                      )}
                    </div>
                  </div>

                  {asset.metadata && Object.keys(asset.metadata).length > 0 && (
                    <div style={{ backgroundColor: '#f9fafb', padding: '16px', borderRadius: '8px' }}>
                      <h4 style={{ fontWeight: '500', marginBottom: '8px' }}>Metadata</h4>
                      <pre style={{ fontSize: '12px', backgroundColor: 'white', padding: '8px', borderRadius: '4px', border: '1px solid #e5e7eb', overflow: 'auto' }}>
                        {JSON.stringify(asset.metadata, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'validation' && (
                <div>
                  {validationReport ? (
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '16px', backgroundColor: '#f9fafb', borderRadius: '8px', marginBottom: '16px' }}>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>
                            {Math.round(validationReport.compliance_score * 100)}%
                          </div>
                          <div style={{ fontSize: '14px', color: '#6b7280' }}>Compliance Score</div>
                        </div>
                        <div style={{ width: '1px', height: '48px', backgroundColor: '#d1d5db' }}></div>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>
                            {validationReport.violations.length}
                          </div>
                          <div style={{ fontSize: '14px', color: '#6b7280' }}>Violations</div>
                        </div>
                      </div>

                      {validationReport.violations.length > 0 && (
                        <div style={{ marginBottom: '16px' }}>
                          <h4 style={{ fontWeight: '500', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                            <AlertTriangle style={{ width: '16px', height: '16px', color: '#f59e0b' }} />
                            Compliance Violations
                          </h4>
                          {validationReport.violations.map((violation, index) => (
                            <div key={index} style={{ border: '1px solid #fed7aa', borderRadius: '8px', padding: '12px', marginBottom: '8px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                                <span style={{ fontWeight: '500' }}>{violation.rule_name}</span>
                                <span style={{ 
                                  padding: '2px 8px', 
                                  fontSize: '12px', 
                                  borderRadius: '9999px',
                                  ...getSeverityColor(violation.severity)
                                }}>
                                  {violation.severity}
                                </span>
                              </div>
                              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>{violation.description}</p>
                              <p style={{ fontSize: '14px', color: '#3b82f6' }}>{violation.recommendation}</p>
                            </div>
                          ))}
                        </div>
                      )}

                      {validationReport.recommendations.length > 0 && (
                        <div>
                          <h4 style={{ fontWeight: '500', marginBottom: '8px' }}>Recommendations</h4>
                          <ul>
                            {validationReport.recommendations.map((rec, index) => (
                              <li key={index} style={{ fontSize: '14px', color: '#6b7280', display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '4px' }}>
                                <span style={{ color: '#3b82f6', marginTop: '4px' }}>•</span>
                                {rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '32px 0', color: '#6b7280' }}>
                      Loading validation report...
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'review' && (
                <div>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '4px' }}>Review Comments</label>
                    <textarea
                      placeholder="Add your review comments..."
                      value={currentComment}
                      onChange={(e) => setCurrentComment(e.target.value)}
                      rows={3}
                      style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }}
                    />
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '4px' }}>Rejection Reason (if rejecting)</label>
                    <textarea
                      placeholder="Explain why this content is being rejected..."
                      value={rejectionReason}
                      onChange={(e) => setRejectionReason(e.target.value)}
                      rows={2}
                      style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }}
                    />
                  </div>

                  <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid #e5e7eb' }} />

                  <div style={{ display: 'flex', gap: '12px' }}>
                    <button
                      onClick={handleApprove}
                      disabled={isLoading}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#10b981',
                        color: 'white',
                        borderRadius: '6px',
                        border: 'none',
                        cursor: isLoading ? 'not-allowed' : 'pointer',
                        opacity: isLoading ? 0.5 : 1,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}
                    >
                      <CheckCircle style={{ width: '16px', height: '16px' }} />
                      Approve
                    </button>
                    <button
                      onClick={handleReject}
                      disabled={isLoading || !rejectionReason.trim()}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#ef4444',
                        color: 'white',
                        borderRadius: '6px',
                        border: 'none',
                        cursor: (isLoading || !rejectionReason.trim()) ? 'not-allowed' : 'pointer',
                        opacity: (isLoading || !rejectionReason.trim()) ? 0.5 : 1,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}
                    >
                      <XCircle style={{ width: '16px', height: '16px' }} />
                      Reject
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 0' }}>
            <div style={{ textAlign: 'center' }}>
              <Eye style={{ width: '48px', height: '48px', color: '#9ca3af', margin: '0 auto 16px' }} />
              <p style={{ color: '#6b7280' }}>Select an asset to review</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AirlockReviewInterface;
