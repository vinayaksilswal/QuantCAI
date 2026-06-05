import { usePageTracking } from '@/hooks/usePageTracking';
import { useEffect } from 'react';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Atom, Calculator, Code, Zap } from 'lucide-react';

declare global {
  interface Window {
    MathJax: any;
  }
}

const QuantumComputing = () => {
  usePageTracking('quantum-computing');
  useEffect(() => {
    // Load MathJax
    const mathJaxScript = document.createElement('script');
    mathJaxScript.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
    mathJaxScript.id = 'MathJax-script';
    mathJaxScript.async = true;
    document.head.appendChild(mathJaxScript);

    // Configure MathJax
    window.MathJax = {
      tex: {
        inlineMath: [['\\(', '\\)']],
        displayMath: [['\\[', '\\]']],
      },
      options: {
        ignoreHtmlClass: 'tex2jax_ignore',
        processHtmlClass: 'tex2jax_process',
      },
    };

    return () => {
      if (mathJaxScript.parentNode) {
        document.head.removeChild(mathJaxScript);
      }
    };
  }, []);

  return (
    <div className="min-h-screen relative">
      <Navbar />
      
      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Understanding of <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Single Qubit</span>
            </h1>
          </div>

          <div className="space-y-12">
            <section>
              <div className="flex items-center mb-6">
                <Atom className="h-8 w-8 text-blue-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Quantum Information</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    Quantum information refers to the field that explores how information can be stored and manipulated using 
                    the principles of quantum mechanics. In classical computing, information is processed in bits, which can 
                    represent either a 0 or a 1. However, in quantum computing, quantum bits or qubits can exist in a superposition 
                    of both 0 and 1 states simultaneously, allowing for parallel computation and potentially solving certain problems 
                    much faster than classical computers.
                  </p>
                  <p className="text-gray-300 leading-relaxed">
                    Quantum information also deals with concepts like entanglement, where the state of one qubit becomes dependent 
                    on the state of another, regardless of the distance between them. This property can be utilized for secure 
                    communication and cryptography, where any eavesdropping would disturb the entangled particles, alerting the 
                    communicating parties.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Calculator className="h-8 w-8 text-purple-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Quantum State Vectors</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    The quantum state of a system is represented by a column vector, similar to probabilistic states. 
                    Vectors representing quantum states are characterized by two properties:
                  </p>
                  <ol className="list-decimal list-inside text-gray-300 mb-6 space-y-2">
                    <li>The entries of a quantum state vector are complex numbers.</li>
                    <li>The sum of the absolute values squared of the entries of the vector is 1.</li>
                  </ol>
                  <p className="text-gray-300 mb-4">
                    The Euclidean norm of a column vector is denoted and defined as follows:
                  </p>
                  <div className="bg-slate-900/50 p-4 rounded-lg mb-4 text-center">
                    <span className="text-blue-400 font-mono text-lg">
                      ||v|| = √(Σ|αₖ|²)
                    </span>
                  </div>
                  <p className="text-gray-300 leading-relaxed">
                    Quantum state vectors are unit vectors concerning the Euclidean norm.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Zap className="h-8 w-8 text-green-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Measuring Quantum States</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    Measuring quantum states is a fundamental aspect of quantum mechanics. A measurement collapses the quantum 
                    state of a system into one of its possible outcomes. For instance, measuring the spin of a particle along 
                    a certain axis might yield "up" or "down." Before measurement, the particle's spin might exist in a superposition 
                    of both states, but upon measurement, it collapses to one state.
                  </p>
                  <p className="text-gray-300 leading-relaxed">
                    The act of measurement is inherently probabilistic, and measuring entangled particles can instantly determine 
                    the state of another, regardless of distance.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Calculator className="h-8 w-8 text-yellow-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Unitary Operations</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed">
                    In quantum mechanics, operations on quantum states are described by unitary transformations, represented by 
                    unitary matrices. These operations preserve the normalization of the quantum state and are reversible. A unitary 
                    matrix U has the property that U†U = I, where U† is the conjugate transpose.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Code className="h-8 w-8 text-blue-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Qiskit Examples</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-6">Starting with Qiskit:</p>
                  
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-blue-400 mb-3">Installation</h4>
                    <div className="bg-slate-900 p-4 rounded-lg">
                      <pre className="text-green-400 text-sm">
{`pip install qiskit
pip install matplotlib
pip install numpy`}
                      </pre>
                    </div>
                  </div>

                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-blue-400 mb-3">Define State Vectors</h4>
                    <div className="bg-slate-900 p-4 rounded-lg overflow-x-auto">
                      <pre className="text-green-400 text-sm">
{`from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
from numpy import sqrt

# Define state vectors
u = Statevector([1 / sqrt(2), 1 / sqrt(2)])
v = Statevector([(1 + 2j) / 3, -2 / 3])
w = Statevector([1 / 3, 2 / 3])

# Display state vectors
display(u.draw("latex"))
display(v.draw("text"))
# [0.33333333+0.66666667j, -0.66666667+0.j]

# Check validity
display(u.is_valid())  # True
display(w.is_valid())  # False

# Measure
v.draw("latex")
v.measure()  # (1, Statevector([0.+0.j, -1.+0.j], dims=(2,)))`}
                      </pre>
                    </div>
                  </div>

                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-blue-400 mb-3">Define Operators</h4>
                    <div className="bg-slate-900 p-4 rounded-lg overflow-x-auto">
                      <pre className="text-green-400 text-sm">
{`from qiskit.quantum_info import Operator

X = Operator([[0, 1], [1, 0]])
Y = Operator([[0, -1.0j], [1.0j, 0]])
Z = Operator([[1, 0], [0, -1]])
H = Operator([[1 / sqrt(2), 1 / sqrt(2)], [1 / sqrt(2), -1 / sqrt(2)]])
S = Operator([[1, 0], [0, 1.0j]])
T = Operator([[1, 0], [0, (1 + 1.0j) / sqrt(2)]])`}
                      </pre>
                    </div>
                  </div>

                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-blue-400 mb-3">Perform Operations</h4>
                    <div className="bg-slate-900 p-4 rounded-lg overflow-x-auto">
                      <pre className="text-green-400 text-sm">
{`v = Statevector([1, 0])
v = v.evolve(H)
v = v.evolve(T)
v = v.evolve(H)
v = v.evolve(T)
v = v.evolve(Z)
v.draw("text")  # [0.85355339+0.35355339j, -0.35355339+0.1464466j]`}
                      </pre>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-lg font-semibold text-blue-400 mb-3">Create Circuits</h4>
                    <div className="bg-slate-900 p-4 rounded-lg overflow-x-auto">
                      <pre className="text-green-400 text-sm">
{`from qiskit import QuantumCircuit
circuit = QuantumCircuit(1)
circuit.h(0)
circuit.t(0)
circuit.h(0)
circuit.t(0)
circuit.z(0)
circuit.draw()

ket0 = Statevector([1, 0])
v = ket0.evolve(circuit)
v.draw("text")  # [0.85355339+0.35355339j, -0.35355339+0.1464466j]`}
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </section>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default QuantumComputing;
