import React from 'react';
import AirlockReviewInterface from '../components/airlock/AirlockReviewInterface';

const AirlockPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Airlock Review System</h1>
          <p className="text-gray-600">Review and approve content before publication</p>
        </div>
        <AirlockReviewInterface />
      </div>
    </div>
  );
};

export default AirlockPage;
