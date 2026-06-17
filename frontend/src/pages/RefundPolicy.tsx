import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { ShieldAlert } from 'lucide-react';

const RefundPolicy = () => {
  return (
    <div className="min-h-screen relative">
      <Navbar />

      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Refund{' '}
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Policy
              </span>
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed">
              QuantCAI Pro Subscription — No Refund Policy
            </p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm rounded-xl p-8 md:p-12 space-y-8">
            <div className="flex items-center justify-center mb-4">
              <div className="bg-red-900/30 border border-red-500/30 rounded-full p-4">
                <ShieldAlert className="h-12 w-12 text-red-400" />
              </div>
            </div>

            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-6 text-center">
              <p className="text-xl font-bold text-white mb-2">ALL SALES ARE FINAL</p>
              <p className="text-gray-300">
                No refunds, credits, exchanges, or chargebacks will be issued.
              </p>
            </div>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Why No Refunds?</h2>
              <p className="text-gray-300 leading-relaxed">
                The QuantCAI Pro Subscription provides <strong className="text-white">immediate, unrestricted access</strong> to
                a proprietary digital SaaS platform, including quantum computing simulation engines, interactive coding
                environments, structured learning paths, and educational courseware hosted at{' '}
                <a href="https://quantcai.in" className="text-blue-400 hover:text-blue-300 underline">quantcai.in</a>.
              </p>
              <p className="text-gray-300 leading-relaxed mt-4">
                Due to the immediate-access, digital nature of this product, all sales are final. Once your access
                credentials have been delivered and your account has been provisioned, the product has been fully
                delivered and cannot be "returned."
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Waiver of Cooling-Off Period</h2>
              <p className="text-gray-300 leading-relaxed">
                By completing your purchase, you expressly waive any right to a cooling-off period or refund, as
                permitted under applicable digital goods legislation, and confirm that you understand you are
                receiving instant access to non-returnable digital services.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Technical Issues</h2>
              <p className="text-gray-300 leading-relaxed">
                If you experience a <strong className="text-white">verifiable technical issue</strong> that completely
                prevents you from accessing the Platform, please contact our support team at{' '}
                <a href="mailto:support@quantcai.in" className="text-blue-400 hover:text-blue-300 underline">
                  support@quantcai.in
                </a>{' '}
                within <strong className="text-white">48 hours</strong> of purchase. We will make every reasonable
                effort to resolve the issue but are under no obligation to issue a refund.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Chargebacks & Disputes</h2>
              <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-6">
                <p className="text-gray-300 leading-relaxed">
                  <strong className="text-yellow-400">⚠ Warning:</strong> Initiating a chargeback or payment dispute
                  without first contacting our support team constitutes a violation of these terms and may result in{' '}
                  <strong className="text-white">immediate account termination</strong> and forfeiture of all access
                  rights.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Agreement</h2>
              <p className="text-gray-300 leading-relaxed">
                By proceeding with your purchase of the QuantCAI Pro Subscription, you confirm that you have read,
                understood, and agreed to this Refund Policy in its entirety.
              </p>
            </section>

            <div className="border-t border-slate-700/50 pt-6 mt-8">
              <p className="text-gray-500 text-sm text-center">
                Last updated: June 2026 · QuantCAI — All rights reserved.
              </p>
              <p className="text-gray-500 text-sm text-center mt-2">
                Questions? Email{' '}
                <a href="mailto:support@quantcai.in" className="text-blue-400 hover:text-blue-300 underline">
                  support@quantcai.in
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default RefundPolicy;
