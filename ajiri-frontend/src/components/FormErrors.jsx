export default function FormErrors({ errors, prefix = 'form' }) {
  if (!Object.keys(errors).length) return null
  return (
    <div role="alert" className="error-text">
      <p>Please check the following:</p>
      <ul>
        {Object.entries(errors).map(([field, messages]) => (
          <li id={`${prefix}-${field}-error`} key={field}>
            <strong>
              {field === 'detail' || field === 'non_field_errors'
                ? 'Request'
                : field.replaceAll('_', ' ')}
              :
            </strong>{' '}
            {messages.join(' ')}
          </li>
        ))}
      </ul>
    </div>
  )
}
