import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Calendar, Users, Video, ExternalLink, Loader2, CheckCircle2, Zap
} from 'lucide-react';
import { usePageTracking } from '@/hooks/usePageTracking';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { useAuth } from '@/hooks/useAuth';
import { axiosClient } from '@/lib/axiosClient';
import { toast } from 'sonner';

interface Cohort {
  id: number;
  title: string;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  capacity: number | null;
  enrollment_status: string;
  zoom_link: string | null;
  is_enrolled: boolean;
}

const DEFAULT_COHORTS: Cohort[] = [
  {
    id: 1,
    title: "Applied Quantum Software Engineering",
    description: "An 8-week intensive program designed for software engineers transitioning to quantum computing and PQC security frameworks. Master Shor's algorithm, VQE, and CBOM compliance.",
    start_date: "2026-08-01T09:00:00Z",
    end_date: "2026-09-26T17:00:00Z",
    capacity: 20,
    enrollment_status: "open",
    zoom_link: null,
    is_enrolled: false
  }
];

export default function Cohorts() {
  usePageTracking('cohorts');
  const navigate = useNavigate();
  const { user } = useAuth();

  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [loadingCohorts, setLoadingCohorts] = useState(true);
  const [enrollingCohortId, setEnrollingCohortId] = useState<number | null>(null);

  const fetchCohorts = async () => {
    if (!user) {
      setCohorts(DEFAULT_COHORTS);
      setLoadingCohorts(false);
      return;
    }
    setLoadingCohorts(true);
    try {
      const response = await axiosClient.get<Cohort[]>('/api/v1/cohorts');
      if (response.data && response.data.length > 0) {
        setCohorts(response.data);
      } else {
        setCohorts(DEFAULT_COHORTS);
      }
    } catch (error: any) {
      console.error('Error fetching cohorts:', error);
      setCohorts(DEFAULT_COHORTS);
    } finally {
      setLoadingCohorts(false);
    }
  };

  useEffect(() => {
    fetchCohorts();

    // Check for PayPal Redirect parameters for cohort capture
    const searchParams = new URLSearchParams(window.location.search);
    const enrollStatus = searchParams.get('enroll');
    const orderToken = searchParams.get('token');
    const courseId = searchParams.get('course');

    if (enrollStatus === 'success' && orderToken && courseId) {
      const captureEnrollment = async () => {
        toast.info('Capturing PayPal payment... Please do not close this window.');
        try {
          await axiosClient.post('/api/v1/cohorts/capture', {
            order_id: orderToken,
            course_id: parseInt(courseId)
          });
          toast.success('You have successfully enrolled in the cohort!');
          
          const cleanUrl = window.location.pathname;
          window.history.replaceState({}, document.title, cleanUrl);
          
          fetchCohorts();
        } catch (err: any) {
          console.error('Capture cohort enrollment error:', err);
          const msg = err.response?.data?.detail || 'Failed to capture PayPal cohort payment.';
          toast.error(msg);
        }
      };
      captureEnrollment();
    } else if (enrollStatus === 'cancel') {
      toast.warning('Cohort enrollment payment cancelled.');
      const cleanUrl = window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    }
  }, [user]);

  const handleEnroll = async (courseId: number) => {
    if (!user) {
      toast.info("Please log in or register to enroll in a cohort.");
      navigate("/login?redirect=/cohorts");
      return;
    }
    
    setEnrollingCohortId(courseId);
    try {
      const response = await axiosClient.post('/api/v1/cohorts/enroll', {
        course_id: courseId
      });
      if (response.data?.url) {
        toast.info("Redirecting to PayPal to complete enrollment...");
        window.location.href = response.data.url;
      } else {
        toast.error("Failed to initiate cohort enrollment payment.");
      }
    } catch (err: any) {
      console.error("Enrollment error:", err);
      const msg = err.response?.data?.detail || "Failed to start enrollment. Please try again.";
      toast.error(msg);
    } finally {
      setEnrollingCohortId(null);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'TBA';
    return new Date(dateStr).toLocaleDateString(undefined, {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="min-h-screen relative bg-transparent text-white">
      <Navbar />
      
      <div className="pt-32 pb-20 px-6 max-w-5xl mx-auto relative z-10">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <span className="px-3 py-1 text-xs font-semibold tracking-wider text-blue-400 uppercase bg-blue-900/30 rounded-full border border-blue-500/20">
              Live Education
            </span>
            <span className="px-3 py-1 text-xs font-semibold tracking-wider text-yellow-400 uppercase bg-yellow-950/30 rounded-full border border-yellow-500/20">
              PayPal Enabled
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4 font-syne">
            Quantum Cohort Programs
          </h1>
          <p className="text-lg text-slate-350 max-w-2xl mx-auto leading-relaxed">
            Collaborative, intensive live training cohorts led by post-quantum security researchers.
          </p>
        </div>

        {loadingCohorts ? (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
        ) : (
          <div className="grid gap-6 max-w-4xl mx-auto">
            {cohorts.map((cohort) => {
              const isEnrolled = cohort.is_enrolled;
              const isEnrolling = enrollingCohortId === cohort.id;
              
              return (
                <Card key={cohort.id} className="relative overflow-hidden bg-slate-900/40 border-slate-800 backdrop-blur-md hover:border-blue-500/40 transition-all duration-300 group shadow-2xl animate-fade-in">
                  <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 opacity-60 group-hover:opacity-100 transition-opacity duration-300" />
                  
                  <CardContent className="p-6 md:p-8 flex flex-col md:flex-row gap-6 md:items-start justify-between">
                    <div className="flex-1 space-y-4">
                      <div>
                        <h3 className="text-2xl font-bold text-white group-hover:text-blue-300 transition-colors duration-200">
                          {cohort.title}
                        </h3>
                        <p className="text-slate-300 mt-2 text-sm leading-relaxed">
                          {cohort.description}
                        </p>
                      </div>
                      
                      <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-400 pt-2 font-mono">
                        <span className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-blue-400" />
                          <span>
                            {formatDate(cohort.start_date)} - {formatDate(cohort.end_date)}
                          </span>
                        </span>
                        <span className="flex items-center gap-2">
                          <Users className="w-4 h-4 text-purple-400" />
                          <span>Capacity: {cohort.capacity || 20} students max</span>
                        </span>
                      </div>

                      <div className="border-t border-slate-800/60 pt-4 mt-2">
                        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 font-mono">Program Curriculum</h4>
                        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs md:text-sm text-slate-350">
                          <li className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                            <span>Weeks 1-2: Qubit Superposition & States</span>
                          </li>
                          <li className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                            <span>Weeks 3-4: Gate Operations & QFT</span>
                          </li>
                          <li className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-pink-400" />
                            <span>Weeks 5-6: Shor's Algorithm & VQE</span>
                          </li>
                          <li className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                            <span>Weeks 7-8: PQC TLS & CBOM Audits</span>
                          </li>
                        </ul>
                      </div>
                    </div>

                    <div className="w-full md:w-64 shrink-0 bg-slate-950/40 p-6 rounded-2xl border border-slate-800 flex flex-col justify-between items-center text-center shadow-lg">
                      <div className="mb-4">
                        <span className="text-xs text-slate-400 uppercase tracking-widest font-semibold font-mono">Tuition Fee</span>
                        <div className="text-3xl font-extrabold text-white mt-1">$1,500.00</div>
                        <span className="text-[10px] text-slate-500 block mt-0.5">One-time payment</span>
                      </div>

                      {isEnrolled ? (
                        <div className="w-full space-y-3">
                          <div className="flex items-center justify-center gap-2 text-emerald-400 font-bold text-sm bg-emerald-500/10 py-2.5 px-4 rounded-xl border border-emerald-500/20">
                            <CheckCircle2 className="w-4 h-4 shrink-0" />
                            <span>Active Enrollment</span>
                          </div>
                          {cohort.zoom_link ? (
                            <Button 
                              onClick={() => window.open(cohort.zoom_link!, '_blank')}
                              className="w-full bg-blue-600 hover:bg-blue-500 text-white gap-2 font-semibold shadow-lg shadow-blue-500/10"
                            >
                              <Video className="w-4 h-4" />
                              <span>Join Zoom Session</span>
                              <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                            </Button>
                          ) : (
                            <p className="text-xs text-slate-500 italic mt-1 font-mono">Live session links will appear here</p>
                          )}
                        </div>
                      ) : (
                        <Button 
                          onClick={() => handleEnroll(cohort.id)}
                          disabled={isEnrolling || cohort.enrollment_status !== 'open'}
                          className={`w-full py-3 h-auto font-bold rounded-xl shadow-lg transition-all ${
                            isEnrolling
                              ? "bg-slate-800 text-slate-400"
                              : cohort.enrollment_status === 'open'
                              ? "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-blue-500/10"
                              : "bg-slate-800 text-slate-500 border-slate-700/50 cursor-not-allowed"
                          }`}
                        >
                          {isEnrolling ? (
                            <span className="flex items-center justify-center gap-2">
                              <Loader2 className="w-4 h-4 animate-spin" />
                              <span>Processing...</span>
                            </span>
                          ) : cohort.enrollment_status === 'open' ? (
                            user ? "Enroll with PayPal" : "Login to Enroll"
                          ) : (
                            "Enrollment Closed"
                          )}
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
      
      <Footer />
    </div>
  );
}
