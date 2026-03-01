export default function PrivacyPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-3xl">
      <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">Data Collection</h2>
        <p className="text-muted-foreground">
          CodeCarbon collects computing emissions data that you explicitly submit
          through our tracking tools. This includes energy consumption metrics,
          hardware information, and geographic region data used to calculate
          carbon emissions.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">Usage</h2>
        <p className="text-muted-foreground">
          Your data is used solely to calculate and display carbon emission
          estimates from your computing activities. We do not sell or share your
          data with third parties for marketing purposes.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">Data Retention</h2>
        <p className="text-muted-foreground">
          Your emissions data is retained for as long as your account is active.
          You may request deletion of your data at any time by contacting us.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">Third Parties</h2>
        <p className="text-muted-foreground">
          We use authentication providers to manage user accounts. No emissions
          data is shared with these providers.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">Your Rights</h2>
        <p className="text-muted-foreground">
          You have the right to access, modify, or delete your personal data.
          Contact us at the email below to exercise these rights.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">Contact</h2>
        <p className="text-muted-foreground">
          For privacy-related inquiries, please open an issue on our{" "}
          <a
            href="https://github.com/mlco2/codecarbon"
            className="text-primary underline"
          >
            GitHub repository
          </a>
          .
        </p>
      </section>
    </div>
  );
}
