import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';

const Privacy = () => {
  return (
    <div className="min-h-screen relative">
      <Navbar />

      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Privacy{' '}
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Policy
              </span>
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed">
              How we collect, use, and protect your personal information.
            </p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm rounded-xl p-8 md:p-12 space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-white mb-4">1. Information We Collect</h2>
              <p className="text-gray-300 leading-relaxed mb-3">
                When you use the QuantCAI platform, we may collect the following types of information:
              </p>
              <ul className="space-y-2 text-gray-300">
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  <span><strong className="text-white">Account Information:</strong> Name, email address, and authentication credentials when you register.</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  <span><strong className="text-white">Payment Information:</strong> Billing details processed securely through our third-party payment processor (PayPal). We do not store credit card numbers.</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  <span><strong className="text-white">Usage Data:</strong> Interaction logs, simulation history, course progress, and feature usage analytics.</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  <span><strong className="text-white">Device Information:</strong> Browser type, IP address, operating system, and device identifiers.</span>
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">2. How We Use Your Information</h2>
              <ul className="space-y-2 text-gray-300">
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  To provide, maintain, and improve the QuantCAI platform and services.
                </li>
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  To process subscriptions, payments, and account management.
                </li>
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  To personalize your learning experience and track course progress.
                </li>
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  To send transactional emails, newsletters (if opted in), and important service updates.
                </li>
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  To detect, prevent, and address technical issues and security threats.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">3. Data Sharing & Third Parties</h2>
              <p className="text-gray-300 leading-relaxed">
                We do not sell or rent your personal information. We may share limited data with trusted third-party
                service providers solely for purposes of payment processing (e.g., PayPal), email delivery,
                hosting, and analytics. All third parties are contractually obligated to protect your data and use it
                only for the services they provide to us.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">4. Cookies & Tracking Technologies</h2>
              <p className="text-gray-300 leading-relaxed">
                We use cookies and similar tracking technologies to enhance your experience, analyze usage patterns,
                and remember your preferences. You can control cookie settings through your browser preferences.
                Disabling certain cookies may limit your ability to use some features of the Platform.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">5. Data Security</h2>
              <p className="text-gray-300 leading-relaxed">
                We implement industry-standard security measures, including encryption (TLS/SSL), secure authentication,
                and access controls to protect your personal information. While no method of electronic storage is 100%
                secure, we continuously monitor and improve our security practices.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">6. Data Retention</h2>
              <p className="text-gray-300 leading-relaxed">
                We retain your personal information for as long as your account is active or as needed to provide you
                services. If you delete your account, we will remove your personal data within 30 days, except where
                retention is required by law or for legitimate business purposes (e.g., fraud prevention, financial
                record-keeping).
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">7. Your Rights</h2>
              <p className="text-gray-300 leading-relaxed mb-3">
                Depending on your jurisdiction, you may have the right to:
              </p>
              <ul className="space-y-2 text-gray-300">
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  Access, correct, or delete your personal data.
                </li>
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  Object to or restrict certain processing of your data.
                </li>
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  Withdraw consent where processing is based on consent.
                </li>
                <li className="flex items-start">
                  <span className="text-blue-400 mr-2 mt-1">•</span>
                  Request data portability in a structured, machine-readable format.
                </li>
              </ul>
              <p className="text-gray-300 leading-relaxed mt-3">
                To exercise any of these rights, contact us at{' '}
                <a href="mailto:support@quantcai.in" className="text-blue-400 hover:text-blue-300 underline">
                  support@quantcai.in
                </a>.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">8. Children's Privacy</h2>
              <p className="text-gray-300 leading-relaxed">
                The QuantCAI platform is not directed at children under the age of 13. We do not knowingly collect
                personal information from children. If we become aware that we have inadvertently collected such data,
                we will take steps to delete it promptly.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">9. Changes to This Policy</h2>
              <p className="text-gray-300 leading-relaxed">
                We may update this Privacy Policy from time to time. Any changes will be posted on this page with
                an updated effective date. We encourage you to review this policy periodically. Your continued use
                of the Platform after any changes constitutes acceptance of the updated policy.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">10. Contact Us</h2>
              <p className="text-gray-300 leading-relaxed">
                If you have any questions or concerns about this Privacy Policy, please contact us at{' '}
                <a href="mailto:support@quantcai.in" className="text-blue-400 hover:text-blue-300 underline">
                  support@quantcai.in
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

export default Privacy;
