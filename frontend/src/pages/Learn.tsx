import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  BookOpen, Atom, Zap, Shield, Globe, Cpu, CheckCircle2, 
  AlertTriangle, ArrowRight, Calendar, Users, Video, 
  ExternalLink, Loader2 
} from 'lucide-react';
import { usePageTracking } from '@/hooks/usePageTracking';
import { SEO } from '@/components/SEO';
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

const Learn = () => {
  usePageTracking('learn');
  const navigate = useNavigate();
  const { user } = useAuth();

  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizCorrect, setQuizCorrect] = useState<boolean | null>(null);

  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [loadingCohorts, setLoadingCohorts] = useState(true);
  const [enrollingCohortId, setEnrollingCohortId] = useState<number | null>(null);

  const quiz = {
    question: "What is the fundamental unit of quantum information that can exist in a superposition of states?",
    options: ["Classical Bit", "Qubit", "Quantum Byte", "Trit"],
    correctIndex: 1
  };

  const fetchCohorts = async () => {
    if (!user) {
      setCohorts(DEFAULT_COHORTS);
      setLoadingCohorts(false);
      return;
    }
    setLoadingCohorts(true);
    try {
      const response = await axiosClient.get<Cohort[]>('/api/v1/cohorts');
      if (Array.isArray(response.data) && response.data.length > 0) {
        setCohorts(response.data);
      } else {
        setCohorts(DEFAULT_COHORTS);
      }
    } catch (error: any) {
      console.error('Error fetching cohorts:', error);
      // Fallback silently to mock cohorts to keep UI functional for all users
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
          
          // Clear query params from URL without refreshing
          const cleanUrl = window.location.pathname;
          window.history.replaceState({}, document.title, cleanUrl);
          
          // Refresh cohorts status
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

  const handleSelectOption = (index: number) => {
    if (quizSubmitted) return;
    setSelectedOption(index);
  };

  const handleSubmitQuiz = () => {
    if (selectedOption === null || quizSubmitted) return;
    const correct = selectedOption === quiz.correctIndex;
    setQuizCorrect(correct);
    setQuizSubmitted(true);
  };

  const handleEnroll = async (courseId: number) => {
    if (!user) {
      toast.info("Please log in or register to enroll in a cohort.");
      navigate("/login?redirect=/learn");
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
    <div className="min-h-screen relative overflow-hidden font-sans bg-transparent text-slate-100 selection:bg-purple-500/30">
      <SEO 
        title="Learn Quantum Computing - QuantCAI Tutorials" 
        description="Master quantum mechanics, quantum circuits, and post-quantum cryptography with our interactive learning platform." 
      />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"></div>
      <Navbar />
      
      <div className="flex pt-32 pb-20 px-6 gap-8 items-stretch max-w-7xl mx-auto">

        {/* Main Content */}
        <div className="flex-1 max-w-4xl mx-auto flex flex-col">
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Welcome to <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">QuantCAI</span>
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed">
              Explore the Frontiers of Computing
            </p>
          </div>

          <Card className="bg-gradient-to-br from-slate-800/80 to-purple-800/80 border-blue-500/30 backdrop-blur-sm mb-12">
            <CardContent className="p-8">
              <p className="text-lg text-gray-300 leading-relaxed">
                Unlock the mysteries of the future with QuantCAI, your portal to the fascinating world of quantum computing. 
                Enter a realm where bits transcend the boundaries of traditional computing and leap into the quantum age.
              </p>
            </CardContent>
          </Card>

          {/* Cohort Programs Section */}
          <section className="mb-16">
            <div className="flex flex-col mb-8">
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 text-xs font-semibold tracking-wider text-blue-400 uppercase bg-blue-900/30 rounded-full border border-blue-500/20">
                  Live Education
                </span>
                <span className="px-3 py-1 text-xs font-semibold tracking-wider text-yellow-400 uppercase bg-yellow-950/30 rounded-full border border-yellow-500/20">
                  PayPal Enabled
                </span>
              </div>
              <h2 className="text-3xl md:text-4xl font-extrabold text-white mt-3 mb-2">
                Quantum Cohort Programs
              </h2>
              <p className="text-slate-400">
                Collaborative, intensive live training cohorts led by post-quantum security researchers.
              </p>
            </div>

            {loadingCohorts ? (
              <div className="flex justify-center items-center py-12">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
              </div>
            ) : (
              <div className="grid gap-6">
                {cohorts.map((cohort) => {
                  const isEnrolled = cohort.is_enrolled;
                  const isEnrolling = enrollingCohortId === cohort.id;
                  
                  return (
                    <Card key={cohort.id} className="relative overflow-hidden bg-slate-900/40 border-slate-800 backdrop-blur-md hover:border-blue-500/40 transition-all duration-300 group">
                      {/* Decorative top gradient border */}
                      <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 opacity-60 group-hover:opacity-100 transition-opacity duration-300" />
                      
                      <CardContent className="p-6 md:p-8 flex flex-col md:flex-row gap-6 md:items-start justify-between">
                        <div className="flex-1 space-y-4">
                          <div>
                            <h3 className="text-2xl font-bold text-white group-hover:text-blue-300 transition-colors duration-200">
                              {cohort.title}
                            </h3>
                            <p className="text-slate-300 mt-2 text-sm md:text-base leading-relaxed">
                              {cohort.description}
                            </p>
                          </div>
                          
                          {/* Details Metadata */}
                          <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs md:text-sm text-slate-400 pt-2">
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

                          {/* Syllabus Overview */}
                          <div className="border-t border-slate-800/60 pt-4 mt-2">
                            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Program Curriculum</h4>
                            <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs md:text-sm text-slate-300">
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

                        {/* Action Box */}
                        <div className="w-full md:w-64 shrink-0 bg-slate-950/40 p-6 rounded-2xl border border-slate-800 flex flex-col justify-between items-center text-center">
                          <div className="mb-4">
                            <span className="text-xs text-slate-400 uppercase tracking-widest font-semibold">Tuition Fee</span>
                            <div className="text-3xl font-extrabold text-white mt-1">$1,500.00</div>
                            <span className="text-xxs text-slate-500 block mt-0.5">One-time payment</span>
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
                                <p className="text-xs text-slate-500 italic mt-1">Live session links will appear here</p>
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
          </section>

          <div className="space-y-12">
            <section>
              <div className="flex items-center mb-6">
                <Cpu className="h-8 w-8 text-blue-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Start Your Quantum Journey with our Interactive Simulator</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    Quantum computing sounds like science fiction, but learning how it works shouldn't require a PhD in physics. If you're a student, hobbyist, or developer curious about the quantum revolution, the biggest hurdle is usually complex math and intimidating code. That's why we built a visual, interactive playground. You don't need to write a single line of code to experience the magic of quantum mechanics—you just need curiosity and a web browser.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Atom className="h-8 w-8 text-purple-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">1. Visual Drag-and-Drop Learning</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    Forget staring at lines of confusing syntax. Our platform uses an intuitive drag-and-drop interface that makes building a quantum circuit as easy as playing with digital building blocks. Simply grab a "gate" (like the Hadamard gate) and drop it onto a qubit wire. Instantly watch how the quantum state changes in real-time, helping you visually grasp abstract concepts.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Zap className="h-8 w-8 text-green-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">2. Experience Real-Time Superposition and Entanglement</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    What exactly is superposition? Instead of reading a textbook definition, see it happen live. As you interact with our simulator, you'll see visualizations of quantum states collapsing and changing. Experiment with entangling two qubits together, so that a change in one instantly affects the other. It's hands-on, visual learning that makes the impossible feel tangible.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Globe className="h-8 w-8 text-blue-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">3. Pre-Built Templates to Get You Started</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    Staring at a blank screen can be overwhelming. We've included a library of beginner-friendly templates ranging from coin-flip probability generators to basic teleportation algorithms. Load a template with one click, run the simulation, and tinker with the gates to see what happens. Learning by doing is the fastest way to become a quantum visionary!
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <Card className="bg-gradient-to-r from-blue-900/40 to-purple-900/40 border-blue-500/50 backdrop-blur-sm">
                <CardContent className="p-8 text-center">
                  <h3 className="text-2xl font-bold text-white mb-4">Ready to leap into the quantum world?</h3>
                  <p className="text-slate-300 mb-6">
                    Discover how easy it is to build your very first quantum algorithm. Create your Free QuantCAI Account today and start experimenting with our interactive simulator!
                  </p>
                  <Button onClick={() => navigate('/signup')} className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-8 rounded-xl shadow-lg shadow-blue-500/20">
                    Create your Free QuantCAI Account <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </CardContent>
              </Card>
            </section>
          </div>

          {/* Quiz Section to Mark Completion */}
          <div className="mt-16 pt-8 border-t border-slate-800">
            <h3 className="text-2xl font-bold text-white mb-6">Concept Check</h3>
            <Card className="bg-slate-900/50 border-slate-800 shadow-2xl">
              <div className="p-6 space-y-5">
                <p className="text-sm font-semibold text-slate-200">
                  {quiz.question}
                </p>

                <div className="space-y-2">
                  {quiz.options.map((opt, oIdx) => {
                    const isSelected = selectedOption === oIdx;
                    return (
                      <button
                        key={oIdx}
                        onClick={() => handleSelectOption(oIdx)}
                        disabled={quizSubmitted}
                        className={`w-full text-left text-xs p-3.5 rounded-xl border transition-all ${
                          isSelected 
                            ? "bg-blue-600/20 border-blue-500 text-white font-medium" 
                            : "bg-slate-950/50 border-slate-800 text-slate-400 hover:bg-slate-900/60 hover:text-white hover:border-slate-700"
                        }`}
                      >
                        {opt
                      }</button>
                    );
                  })}
                </div>

                {quizSubmitted ? (
                  <div className={`p-4 rounded-xl border flex gap-3 text-xs leading-relaxed ${
                    quizCorrect 
                      ? "bg-emerald-950/20 border-emerald-900/50 text-emerald-300" 
                      : "bg-rose-950/20 border-rose-900/50 text-rose-300"
                  }`}>
                    {quizCorrect ? (
                      <div className="w-full flex items-center justify-between">
                        <div className="flex gap-3">
                          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                          <div>
                            <p className="font-bold">Correct!</p>
                            <p className="mt-0.5">You have mastered the basics of Quantum Computing.</p>
                          </div>
                        </div>
                        <Button 
                          onClick={() => navigate('/quantum-computing')}
                          className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2 animate-bounce"
                        >
                          Next: Quantum Basics <ArrowRight className="w-4 h-4" />
                        </Button>
                      </div>
                    ) : (
                      <>
                        <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
                        <div>
                          <p className="font-bold">Incorrect</p>
                          <p className="mt-0.5">Review the sections above to try again. (Refresh to retry)</p>
                        </div>
                      </>
                    )}
                  </div>
                ) : (
                  <Button
                    onClick={handleSubmitQuiz}
                    disabled={selectedOption === null}
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-xl font-bold shadow-lg shadow-blue-500/10"
                  >
                    Submit Answer
                  </Button>
                )}
              </div>
            </Card>
          </div>
        </div>


      </div>

      <Footer />
    </div>
  );
};

export default Learn;
