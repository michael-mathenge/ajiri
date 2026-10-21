const labels = {
  email: 'Email',
  password: 'Password',
  full_name: 'Full name',
  phone_number: 'Phone number',
  cv_file: 'CV file',
  skill_names: 'Skills',
  expected_revision: 'CV revision',
  content_sha256: 'CV content',
  detail: 'Request',
  non_field_errors: 'Request',
}

// Preserve caller error IDs while making DRF keys readable to people.
// see docs/CONCEPTS.md#readable-form-errors
export default function FormErrors({
  errors,
  prefix = 'form',
  className = '',
}) {
  if (!Object.keys(errors).length) return null
  return (
    <div role="alert" className={`error-text ${className}`}>
      <p>Please check the following:</p>
      <ul className="mt-3 space-y-3">
        {Object.entries(errors).map(([field, messages]) => (
          <li id={`${prefix}-${field}-error`} key={field}>
            <strong>
              {labels[field] ||
                field.charAt(0).toUpperCase() +
                  field
                    .slice(1)
                    .replaceAll('_', ' ')
                    .replace(
                      /\.(\d+)(?=\.|$)/g,
                      (_, index) => ` ${Number(index) + 1}`
                    )
                    .replaceAll('.', ' - ')}
              :
            </strong>{' '}
            <ul className="mt-1 space-y-1">
              {messages.map((message, index) => (
                <li key={index}>{message} </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  )
}
