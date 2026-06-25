import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';

const Terms = () => {
  return (
    <div className="min-h-screen relative">
      <Navbar />

      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Terms &{' '}
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Conditions
              </span>
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed">
              Please read these terms carefully before using the QuantCAI platform.
            </p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm rounded-xl p-8 md:p-12 space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-white mb-4">1. Acceptance of Terms</h2>
              <p className="text-gray-300 leading-relaxed">
                By accessing or using the QuantCAI platform (quantcai.in), including all associated services,
                simulation tools, educational materials, and coding environments (collectively, the "Platform"),
                you agree to be bound by these Terms & Conditions. If you do not agree to these terms, do not
                use the Platform.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">2. Description of Service</h2>
              <p className="text-gray-300 leading-relaxed">
                QuantCAI provides a full-stack Software-as-a-Service (SaaS) platform offering quantum computing
                simulations, interactive coding environments, structured learning paths, and educational courseware.
                The Platform is built using React, Node.js, Python, and FastAPI.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">3. Subscription & Payment</h2>
              <p className="text-gray-300 leading-relaxed">
                The QuantCAI Pro Subscription provides immediate, unrestricted access to all premium features of
                the Platform upon successful payment. Subscription fees are billed on a recurring basis as described
                at the point of purchase. You are responsible for all charges incurred under your account.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">4. Refund Policy — All Sales Final</h2>
              <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-6">
                <p className="text-gray-300 leading-relaxed">
                  Due to the immediate-access, digital nature of this product, <strong className="text-white">ALL
                  SALES ARE FINAL</strong>. No refunds, credits, exchanges, or chargebacks will be issued under any
                  circumstances once access credentials have been delivered and the account has been provisioned.
                </p>
                <p className="text-gray-300 leading-relaxed mt-4">
                  By completing your purchase, you expressly waive any right to a cooling-off period or refund, as
                  permitted under applicable digital goods legislation, and confirm that you understand you are
                  receiving instant access to non-returnable digital services.
                </p>
                <p className="text-gray-300 leading-relaxed mt-4">
                  If you experience a verifiable technical issue that prevents you from accessing the Platform entirely,
                  please contact our support team at{' '}
                  <a href="mailto:support@quantcai.in" className="text-blue-400 hover:text-blue-300 underline">
                    support@quantcai.in
                  </a>{' '}
                  within 48 hours of purchase. We will make every reasonable effort to resolve the issue but are under
                  no obligation to issue a refund.
                </p>
                <p className="text-gray-300 leading-relaxed mt-4">
                  Initiating a chargeback or payment dispute without first contacting our support team constitutes a
                  violation of these terms and may result in immediate account termination and forfeiture of all access
                  rights.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">5. AI Disclosure</h2>
              <p className="text-gray-300 leading-relaxed">
                Artificial intelligence tools were utilized during the development of the QuantCAI platform to assist
                with full-stack code optimization, performance tuning, and the drafting of foundational educational
                and instructional materials. However, the entire platform — including all quantum simulation engines,
                backend infrastructure, frontend interfaces, API integrations, and published educational content — has
                been rigorously tested, manually audited, and finalized by a qualified human developer. All AI-generated
                outputs were reviewed, refined, and validated for accuracy, security, and pedagogical integrity before
                deployment.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">6. Intellectual Property</h2>
              <p className="text-gray-300 leading-relaxed">
                All content, code, simulation algorithms, educational materials, graphics, and proprietary tools
                available on the Platform are the intellectual property of QuantCAI and are protected by applicable
                copyright and intellectual property laws. You may not reproduce, distribute, modify, or create
                derivative works without express written permission.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">7. Enterprise SLAs and Uptime Guarantees</h2>
              <p className="text-gray-300 leading-relaxed">
                For users on our "Enterprise" tier, we guarantee a 99.9% uptime for core simulation APIs and Post-Quantum Cryptography scanning endpoints. In the event of an outage exceeding SLA thresholds, pro-rated service credits will be issued according to your specific Enterprise contract. Free, Pro, and Developer API tiers are provided "as-is" without a binding uptime SLA, though we continually monitor and maintain highly available infrastructure.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">8. User Conduct</h2>
              <p className="text-gray-300 leading-relaxed">
                You agree not to misuse the Platform, attempt to gain unauthorized access to any systems, interfere
                with other users' access, reverse-engineer any proprietary tools or algorithms, or use the Platform
                for any unlawful purpose. Violations may result in immediate account termination.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">9. Limitation of Liability</h2>
              <p className="text-gray-300 leading-relaxed">
                QuantCAI shall not be liable for any indirect, incidental, special, consequential, or punitive
                damages arising out of your use of or inability to use the Platform. Our total liability shall not
                exceed the amount paid by you for the subscription in the twelve (12) months preceding the claim.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">10. Modifications to Terms</h2>
              <p className="text-gray-300 leading-relaxed">
                QuantCAI reserves the right to modify these Terms & Conditions at any time. Changes will be posted
                on this page with an updated effective date. Your continued use of the Platform after any modifications
                constitutes acceptance of the updated terms.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">11. Legal & Compliance Contact</h2>
              <p className="text-gray-300 leading-relaxed">
                For any questions regarding these Terms & Conditions, SLAs, or Enterprise compliance, please contact us at{' '}
                <a href="mailto:legal@quantcai.in" className="text-blue-400 hover:text-blue-300 underline">
                  legal@quantcai.in
                </a>.
              </p>
            </section>

            <div className="border-t border-slate-700/50 pt-6 mt-8">
              <p className="text-gray-500 text-sm text-center">
                Last updated: June 2026 · QuantCAI — All rights reserved.
              </p>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default Terms;
