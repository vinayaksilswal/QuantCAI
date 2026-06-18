import { useState, useRef } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  FolderGit2, UploadCloud, FileArchive, ShieldAlert, CheckCircle2, 
  AlertTriangle, Loader2, RefreshCw, HelpCircle, Code, ChevronRight,
  Sparkles
} from 'lucide-react';
import { usePageTracking } from '@/hooks/usePageTracking';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { axiosClient } from '@/lib/axiosClient';
import { toast } from 'sonner';

interface Vulnerability {
  file: string;
  line: number;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  description: string;
  remediation: string;
}

interface ScanResult {
  files_scanned: number;
  pqc_readiness_pct: number;
  overall_risk_score: number;
  summary: {
    total_findings: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  vulnerabilities: Vulnerability[];
}

const RepoScanner = () => {
  usePageTracking('repo_scanner');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [patches, setPatches] = useState<Record<number, string>>({});
  const [refactoringId, setRefactoringId] = useState<number | null>(null);

  const [badgeTargetId, setBadgeTargetId] = useState<number | null>(null);
  const [generatingBadge, setGeneratingBadge] = useState(false);

  const generateBadge = async () => {
    if (!selectedFile) return;
    setGeneratingBadge(true);
    try {
      const response = await axiosClient.post<{ id: number }>('/api/v1/pqc/monitored-targets', {
        target_type: 'repository',
        target_value: selectedFile.name,
        schedule_interval: 'weekly'
      });
      setBadgeTargetId(response.data.id);
      toast.success('Monitored repository configured and badge generated!');
    } catch (err: any) {
      console.error(err);
      toast.error('Failed to configure badge: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGeneratingBadge(false);
    }
  };

  const handleAIRefactor = async (vuln: Vulnerability, idx: number) => {
    if (!vuln.content) {
      toast.error("File content is missing for this vulnerability.");
      return;
    }
    setRefactoringId(idx);
    try {
      const response = await axiosClient.post('/api/v1/ast/refactor', {
        filename: vuln.file,
        content: vuln.content,
        line_no: vuln.line,
        issue_title: vuln.title
      });
      setPatches(prev => ({
        ...prev,
        [idx]: response.data.patch
      }));
      toast.success("AI refactoring patch generated successfully.");
    } catch (err: any) {
      console.error("Refactoring error:", err);
      const msg = err.response?.data?.detail || "Failed to generate refactoring suggestions.";
      toast.error(msg);
    } finally {
      setRefactoringId(null);
    }
  };


  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
      } else {
        toast.error("Please upload a valid ZIP archive of your repository.");
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
      } else {
        toast.error("Please select a ZIP archive.");
      }
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const startScan = async () => {
    if (!selectedFile) return;

    setIsScanning(true);
    setResult(null);
    setPatches({});
    setBadgeTargetId(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axiosClient.post<ScanResult>('/api/v1/ast/scan-zip', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setResult(response.data);
      toast.success("Codebase AST scan completed successfully.");
    } catch (err: any) {
      console.error("AST Scan error:", err);
      const msg = err.response?.data?.detail || "Failed to parse repository source files.";
      toast.error(msg);
    } finally {
      setIsScanning(false);
    }
  };

  const clearScan = () => {
    setSelectedFile(null);
    setResult(null);
    setPatches({});
    setBadgeTargetId(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };


  const getSeverityBadgeColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-500/10 border-red-500/30 text-red-400';
      case 'HIGH':
        return 'bg-orange-500/10 border-orange-500/30 text-orange-400';
      case 'MEDIUM':
        return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400';
      case 'LOW':
        return 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400';
      default:
        return 'bg-slate-500/10 border-slate-500/30 text-slate-400';
    }
  };

  const filteredVulnerabilities = result?.vulnerabilities.filter(v => {
    if (filterSeverity === 'ALL') return true;
    return v.severity === filterSeverity;
  }) || [];

  return (
    <div className="min-h-screen relative bg-transparent text-white">
      <Navbar />

      <div className="pt-32 pb-24 px-6 max-w-7xl mx-auto flex flex-col gap-8">
        
        {/* Header */}
        <div className="max-w-3xl">
          <div className="flex items-center gap-2 mb-3">
            <span className="px-3 py-1 text-xs font-semibold tracking-wider text-purple-400 uppercase bg-purple-900/30 rounded-full border border-purple-500/20">
              Enterprise AST Audit
            </span>
            <span className="px-3 py-1 text-xs font-semibold tracking-wider text-blue-400 uppercase bg-blue-900/30 rounded-full border border-blue-500/20">
              Compliance-Ready
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold font-syne text-white leading-tight">
            Repository <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Cryptographic Scanner</span>
          </h1>
          <p className="text-slate-400 text-lg mt-3">
            Analyze your project's codebase statically for quantum-vulnerable public key interfaces, elliptic curve parameters, and legacy TLS libraries.
          </p>
        </div>

        {/* Scan Upload Section */}
        {!result && (
          <Card className="bg-slate-900/40 border-slate-800 backdrop-blur-md overflow-hidden relative">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-blue-500 to-purple-500 opacity-60" />
            <CardContent className="p-8 md:p-12">
              <div 
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={selectedFile ? undefined : triggerFileInput}
                className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer flex flex-col items-center justify-center ${
                  dragActive 
                    ? "border-blue-500 bg-blue-500/5" 
                    : selectedFile 
                    ? "border-slate-800 bg-slate-950/20 cursor-default" 
                    : "border-slate-800 hover:border-slate-700 bg-slate-950/30 hover:bg-slate-950/40"
                }`}
              >
                <input 
                  ref={fileInputRef}
                  type="file"
                  accept=".zip"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                {selectedFile ? (
                  <div className="space-y-6 max-w-md w-full">
                    <div className="flex justify-center">
                      <div className="p-4 bg-blue-500/10 rounded-2xl border border-blue-500/20 text-blue-400 animate-pulse">
                        <FileArchive className="w-16 h-16" />
                      </div>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white truncate">{selectedFile.name}</h3>
                      <p className="text-sm text-slate-400 mt-1">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready to analyze</p>
                    </div>

                    <div className="flex gap-4">
                      <Button 
                        onClick={clearScan}
                        variant="outline" 
                        disabled={isScanning}
                        className="flex-1 bg-transparent border-slate-800 hover:bg-slate-900 hover:text-white"
                      >
                        Change File
                      </Button>
                      <Button 
                        onClick={startScan}
                        disabled={isScanning}
                        className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold"
                      >
                        {isScanning ? (
                          <span className="flex items-center gap-2">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Parsing AST...</span>
                          </span>
                        ) : (
                          "Start Audit"
                        )}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4 max-w-sm">
                    <div className="flex justify-center">
                      <div className="p-4 bg-slate-900/80 rounded-2xl border border-slate-800/80 text-slate-400 group-hover:text-white transition-colors duration-200">
                        <UploadCloud className="w-12 h-12" />
                      </div>
                    </div>
                    <div>
                      <p className="font-bold text-white text-lg">Upload codebase archive</p>
                      <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                        Drag and drop your project's ZIP folder here, or click to browse. Max size 50MB. Only source files (.py, .java, .go, .c, .cpp) are parsed.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Scan Results dashboard */}
        {result && (
          <div className="space-y-8 animate-fade-in">
            {/* Top Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              
              {/* Score Card */}
              <Card className="bg-slate-900/40 border-slate-800 backdrop-blur-md relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-blue-500 to-teal-500" />
                <CardContent className="p-6 text-center">
                  <span className="text-xs text-slate-400 font-semibold tracking-wider uppercase">PQC Readiness Score</span>
                  <div className="text-4xl font-extrabold text-white mt-2 mb-1">{result.pqc_readiness_pct}%</div>
                  <span className="text-xxs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold uppercase tracking-wider">
                    {result.pqc_readiness_pct > 80 ? 'Grade A' : result.pqc_readiness_pct > 50 ? 'Grade C' : 'Grade F'}
                  </span>
                </CardContent>
              </Card>

              {/* Scanned Card */}
              <Card className="bg-slate-900/40 border-slate-800 backdrop-blur-md">
                <CardContent className="p-6 text-center">
                  <span className="text-xs text-slate-400 font-semibold tracking-wider uppercase">Files Processed</span>
                  <div className="text-4xl font-extrabold text-white mt-2 mb-1">{result.files_scanned}</div>
                  <span className="text-xxs text-slate-400 flex items-center justify-center gap-1">
                    <Code className="w-3.5 h-3.5" /> Source code files parsed
                  </span>
                </CardContent>
              </Card>

              {/* Findings Card */}
              <Card className="bg-slate-900/40 border-slate-800 backdrop-blur-md relative overflow-hidden">
                {result.summary.total_findings > 0 && (
                  <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-orange-500 to-red-500" />
                )}
                <CardContent className="p-6 text-center">
                  <span className="text-xs text-slate-400 font-semibold tracking-wider uppercase">Vulnerability Findings</span>
                  <div className="text-4xl font-extrabold text-white mt-2 mb-1">{result.summary.total_findings}</div>
                  <span className={`text-xxs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                    result.summary.total_findings === 0 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                      : 'bg-red-500/10 text-red-400 border border-red-500/20'
                  }`}>
                    {result.summary.total_findings === 0 ? 'Compliant' : 'Vulnerable'}
                  </span>
                </CardContent>
              </Card>

              {/* Reset Controller */}
              <Card className="bg-slate-900/40 border-slate-800 backdrop-blur-md flex items-center justify-center">
                <CardContent className="p-6 text-center w-full">
                  <Button 
                    onClick={clearScan}
                    variant="outline"
                    className="w-full bg-transparent border-slate-800 hover:bg-slate-950 text-white font-bold h-12 rounded-xl gap-2 transition-all hover:scale-102"
                  >
                    <RefreshCw className="w-4 h-4" /> Scan Another Repo
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Showcase Public Compliance Badge */}
            <Card className="bg-slate-900/40 border-slate-800 backdrop-blur-md relative overflow-hidden">
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                  <div className="space-y-1 max-w-xl">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-purple-400" />
                      Showcase Your Security Posture
                    </h3>
                    <p className="text-xs text-slate-400 leading-relaxed font-mono">
                      Configure a scheduled compliance target for this repository to monitor cryptographic drift, verify certificates, and generate a dynamic SVG badge for your GitHub README.
                    </p>
                  </div>
                  
                  {!badgeTargetId ? (
                    <Button
                      onClick={generateBadge}
                      disabled={generatingBadge}
                      className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold h-10 px-6 shrink-0"
                    >
                      {generatingBadge ? "Enabling Badge..." : "Enable Compliance Badge"}
                    </Button>
                  ) : (
                    <div className="flex flex-col md:flex-row items-stretch md:items-center gap-4 w-full md:w-auto flex-1 max-w-xl">
                      <div className="flex items-center gap-3 bg-slate-950/60 p-2 rounded-xl border border-slate-850 justify-between md:justify-start shrink-0">
                        <span className="text-[10px] text-slate-500 font-mono pl-1">Live Badge:</span>
                        <img
                          src={`/api/v1/public/badge/${badgeTargetId}`}
                          alt="PQC Compliance Badge"
                          className="h-5 pr-1"
                        />
                      </div>
                      
                      <div className="flex-1 flex gap-2">
                        <input
                          readOnly
                          value={`[![PQC Readiness](${window.location.origin}/api/v1/public/badge/${badgeTargetId})](${window.location.origin}/repo-scanner)`}
                          className="flex-1 bg-slate-950/60 border border-slate-850 rounded px-2.5 py-1.5 text-[10px] font-mono text-slate-400 select-all focus:outline-none"
                        />
                        <Button
                          size="sm"
                          className="bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white px-3"
                          onClick={() => {
                            navigator.clipboard.writeText(`[![PQC Readiness](${window.location.origin}/api/v1/public/badge/${badgeTargetId})](${window.location.origin}/repo-scanner)`);
                            toast.success("Markdown copied to clipboard!");
                          }}
                        >
                          Copy
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Severity Breakdowns */}
            <div className="flex flex-wrap gap-4 items-center">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest mr-2">Filters:</span>
              <button 
                onClick={() => setFilterSeverity('ALL')}
                className={`px-4 py-2 text-xs font-bold rounded-xl border transition-all ${
                  filterSeverity === 'ALL' 
                    ? 'bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-500/10' 
                    : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-white'
                }`}
              >
                All ({result.summary.total_findings})
              </button>
              <button 
                onClick={() => setFilterSeverity('CRITICAL')}
                disabled={result.summary.critical === 0}
                className={`px-4 py-2 text-xs font-bold rounded-xl border transition-all ${
                  filterSeverity === 'CRITICAL' 
                    ? 'bg-red-600 border-red-500 text-white shadow-lg shadow-red-500/10' 
                    : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-red-500/30 hover:text-red-400 disabled:opacity-40 disabled:cursor-not-allowed'
                }`}
              >
                Critical ({result.summary.critical})
              </button>
              <button 
                onClick={() => setFilterSeverity('HIGH')}
                disabled={result.summary.high === 0}
                className={`px-4 py-2 text-xs font-bold rounded-xl border transition-all ${
                  filterSeverity === 'HIGH' 
                    ? 'bg-orange-600 border-orange-500 text-white shadow-lg shadow-orange-500/10' 
                    : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-orange-500/30 hover:text-orange-400 disabled:opacity-40 disabled:cursor-not-allowed'
                }`}
              >
                High ({result.summary.high})
              </button>
              <button 
                onClick={() => setFilterSeverity('MEDIUM')}
                disabled={result.summary.medium === 0}
                className={`px-4 py-2 text-xs font-bold rounded-xl border transition-all ${
                  filterSeverity === 'MEDIUM' 
                    ? 'bg-yellow-600 border-yellow-500 text-white shadow-lg shadow-yellow-500/10' 
                    : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-yellow-500/30 hover:text-yellow-400 disabled:opacity-40 disabled:cursor-not-allowed'
                }`}
              >
                Medium ({result.summary.medium})
              </button>
              <button 
                onClick={() => setFilterSeverity('LOW')}
                disabled={result.summary.low === 0}
                className={`px-4 py-2 text-xs font-bold rounded-xl border transition-all ${
                  filterSeverity === 'LOW' 
                    ? 'bg-cyan-600 border-cyan-500 text-white shadow-lg shadow-cyan-500/10' 
                    : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-cyan-500/30 hover:text-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed'
                }`}
              >
                Low ({result.summary.low})
              </button>
            </div>

            {/* Findings List */}
            <div className="space-y-4">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <FolderGit2 className="w-5 h-5 text-blue-400" />
                <span>Vulnerability Breakdown ({filteredVulnerabilities.length})</span>
              </h3>

              {filteredVulnerabilities.length === 0 ? (
                <Card className="bg-slate-950/20 border-slate-800 py-12 text-center text-slate-400">
                  <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
                  <p className="font-bold text-white">No vulnerabilities found matching this filter!</p>
                  <p className="text-xs mt-1">Your code meets the current post-quantum cryptography standards.</p>
                </Card>
              ) : (
                <div className="grid gap-4">
                  {filteredVulnerabilities.map((vuln, idx) => (
                    <Card key={idx} className="bg-slate-900/20 border-slate-800 hover:border-slate-700 transition-colors duration-200">
                      <CardContent className="p-6 flex flex-col md:flex-row md:items-start justify-between gap-6">
                        <div className="space-y-3 flex-1">
                          
                          {/* File Details */}
                          <div className="flex flex-wrap items-center gap-3">
                            <span className={`px-2.5 py-0.5 text-xxs font-extrabold uppercase tracking-wider rounded border ${getSeverityBadgeColor(vuln.severity)}`}>
                              {vuln.severity}
                            </span>
                            <code className="text-slate-400 text-xs font-mono font-bold bg-slate-950/60 px-2.5 py-1 rounded border border-slate-850">
                              {vuln.file} : L{vuln.line}
                            </code>
                          </div>

                          {/* Vulnerability Title */}
                          <h4 className="text-lg font-bold text-white">
                            {vuln.title}
                          </h4>

                          {/* Description */}
                          <p className="text-sm text-slate-300 leading-relaxed">
                            {vuln.description}
                          </p>

                          {/* Remediation Block */}
                          <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-850 flex gap-3 text-xs leading-relaxed text-slate-300">
                            <ShieldAlert className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
                            <div>
                              <span className="font-bold text-purple-300 block mb-0.5">Remediation Blueprint</span>
                              <span>{vuln.remediation}</span>
                            </div>
                          </div>

                          {/* AI Refactor Button */}
                          {vuln.content && (
                            <div className="mt-4 flex flex-col gap-3">
                              <div>
                                <Button
                                  onClick={() => handleAIRefactor(vuln, idx)}
                                  disabled={refactoringId === idx}
                                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-xs font-bold gap-2 h-9 px-4 rounded-xl"
                                >
                                  {refactoringId === idx ? (
                                    <>
                                      <Loader2 className="w-4 h-4 animate-spin" />
                                      <span>Generating Post-Quantum Patch...</span>
                                    </>
                                  ) : (
                                    <>
                                      <Sparkles className="w-4 h-4" />
                                      <span>Request AI Code Remediation</span>
                                    </>
                                  )}
                                </Button>
                              </div>

                              {patches[idx] && (
                                <div className="mt-2 bg-slate-950/80 rounded-xl p-5 border border-slate-800 font-mono text-xs overflow-x-auto relative">
                                  <div className="flex justify-between items-center mb-3 pb-2 border-b border-slate-800">
                                    <span className="text-[10px] text-purple-400 uppercase tracking-widest font-extrabold flex items-center gap-1.5">
                                      <Code className="w-3.5 h-3.5" /> AI Unified Git Diff Patch
                                    </span>
                                    <Button 
                                      onClick={() => {
                                        navigator.clipboard.writeText(patches[idx]);
                                        toast.success("Patch copied to clipboard!");
                                      }}
                                      variant="outline"
                                      className="h-7 px-3 bg-slate-900 border-slate-800 hover:bg-slate-800 hover:text-white text-[10px] font-bold"
                                    >
                                      Copy Patch
                                    </Button>
                                  </div>
                                  <pre className="text-slate-300 leading-relaxed whitespace-pre font-mono overflow-auto max-h-[350px]">
                                    {patches[idx]}
                                  </pre>
                                </div>
                              )}
                            </div>
                          )}
                        </div>


                        {/* Reference Badge */}
                        <div className="w-full md:w-56 shrink-0 bg-slate-950/20 p-4 rounded-xl border border-slate-850 flex flex-col justify-center items-start text-xs">
                          <span className="text-slate-400 font-semibold uppercase tracking-widest text-[10px] mb-1.5">Compliance Standard</span>
                          <span className="text-slate-200 flex items-center gap-1.5 font-bold">
                            <HelpCircle className="w-4 h-4 text-blue-400" />
                            <span>NIST FIPS 203/204</span>
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
};

export default RepoScanner;
