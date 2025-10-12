import { useState } from "react";
import { Download, Eye, X } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { logger } from "../utils/logger";

interface LogEntry {
  timestamp: string;
  level: string;
  category: string;
  message: string;
  data?: any;
}

export function LogViewer() {
  const [isOpen, setIsOpen] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const handleViewLogs = () => {
    const allLogs = logger.getLogs();
    setLogs(allLogs);
    setIsOpen(true);
  };

  const formatLogEntry = (log: LogEntry): string => {
    const time = new Date(log.timestamp).toLocaleTimeString();
    const levelEmoji = {
      debug: '🐛',
      info: 'ℹ️',
      warn: '⚠️',
      error: '❌'
    }[log.level] || 'ℹ️';
    
    let formatted = `${time} | ${levelEmoji} ${log.level.toUpperCase()} | ${log.category.toUpperCase()} | ${log.message}`;
    
    if (log.data && Object.keys(log.data).length > 0) {
      formatted += ` | ${JSON.stringify(log.data)}`;
    }
    
    return formatted;
  };

  const handleDownloadLogs = () => {
    logger.downloadLogs();
  };

  const handleClearLogs = () => {
    logger.clearLogs();
    setLogs([]);
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-4 right-4 flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleViewLogs}
          className="shadow-lg"
        >
          <Eye className="w-4 h-4 mr-2" />
          View Logs
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleDownloadLogs}
          className="shadow-lg"
        >
          <Download className="w-4 h-4 mr-2" />
          Download Logs
        </Button>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-4xl max-h-[80vh] flex flex-col p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Frontend Logs</h2>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadLogs}
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearLogs}
            >
              Clear
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(false)}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto bg-gray-900 text-gray-100 p-4 rounded font-mono text-xs">
          {logs.length === 0 ? (
            <p className="text-gray-400">No logs yet</p>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="mb-1 whitespace-pre-wrap break-all">
                {formatLogEntry(log)}
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}

