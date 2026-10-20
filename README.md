# Email Reputation Circuit Breaker

This example demonstrates a reputation circuit breaker system for an email platform. It simulates multiple tenants sending emails, tracks their reputation based on spam complaints and bounces, and automatically 'trips' the circuit to block sending for tenants whose reputation falls below a threshold. It also shows how a circuit can transition to a 'half-open' state to attempt recovery after a cooldown period.

## Language

`python`

## How to Run

Save the code as `main.py`. Run from your terminal: `python main.py`

## Original Article

This example accompanies the Turkish article: [Tek Bir Kötü Kiracı Tüm E-posta Platformunuzu Batırabilir: İtibar Devre Kesici Nasıl Kurulur?](https://fatihsoysal.com/blog/tek-bir-kotu-kiraci-tum-e-posta-platformunuzu-batirabilir-itibar-devre-kesici-nasil-kurulur/).

## License

MIT — see [LICENSE](LICENSE).
