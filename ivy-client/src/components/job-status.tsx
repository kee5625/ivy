import React from 'react';

interface JobStatusProps {
    jobId: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress?: number;
    message?: string;
}

export const JobStatus: React.FC<JobStatusProps> = ({
    jobId,
    status,
    progress = 0,
    message = '',
}) => {
    const getStatusColor = () => {
        switch (status) {
            case 'pending':
                return 'text-gray-500';
            case 'running':
                return 'text-blue-500';
            case 'completed':
                return 'text-green-500';
            case 'failed':
                return 'text-red-500';
            default:
                return 'text-gray-500';
        }
    };

    return (
        <div className="p-4 border rounded-lg">
            <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold">Job {jobId}</h3>
                <span className={`font-medium ${getStatusColor()}`}>{status}</span>
            </div>
            
            {progress > 0 && (
                <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            )}
            
            {message && <p className="text-sm text-gray-600">{message}</p>}
        </div>
    );
};