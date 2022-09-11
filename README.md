# Sistema de Orquestación de Telemetría de `PAGODA`

En el ámbito del proyecto `PAGODA` (_Plataforma Automática de GestiÓn DistribuidA_), se ha diseñado un sistema para orquestar la recolección y agregación de datos de telemetría, denominado Orquestador de Telemetría, que permita obtener información de rendimiento de los servicios virtualizados desplegados en la infraestructura de red _Edge Computing_ de `PAGODA` a través de la instanciación de plataformas de monitorización basadas en el stack de [`Prometheus`](https://Prometheus.io/). En la siguiente figura se muestra una representación a alto nivel de la arquitectura del sistema de orquestación de telemetría propuesto.

![Telemetry Orchestration](docs/images/`PAGODA`_telemetry_orchestration-telemetry-distributed-scenario.png)

Como se puede observar en la figura, existe un componente central denominado `Telemetry Orchestrator` que se encarga de orquestar el proceso de recolección y agregación de datos de telemetría. Este componente tiene una API basada en REST y con [especificación OpenAPI](utils/openapi-spec/telemetry-api.json) que permite al operador del sistema determinar qué información de telemetría desea recopilar, con qué frecuencia y a partir de qué sede concreta (es decir, _Ática_, _Económicas_ o _Pleiades_) desea obtenerla. Una vez el operador indica la información de telemetría a monitorizar (en concreto, información de telemetría relativa a métricas proporcionadas desde la plataforma de monitorización Prometheus), el componente `Telemetry Orchestrator` guarda la información de la solicitud en una base de datos (_Telemetry DB_ en la figura) y se activa y automatiza el proceso de recolección y agregación de datos de telemetría en la sede pertinente. Aquí es donde entra en juego el papel del componente `Telemetry Aggregator` de cada sede de la infraestructura de red de `PAGODA`. Este componente se encarga de gestionar el ciclo de vida del procedimiento de recolección y agregación de métricas de Prometheus. Tiene dos entidades básicas y fundamentales: _Collector Agent_ y _Kafka Broker_. El _Collector_ Agent está basado en una solución de [Apache NiFi](https://nifi.apache.org/) y es la entidad que se encarga de automatizar el proceso de recolección de datos de telemetría de Prometheus según el intervalo de muestreo indicado. Esta entidad permite además realizar un procesamiento adicional para limpieza y estructuración de los datos de telemetría que conlleva la normalización de los datos de telemetría según un modelo [YANG](https://www.rfc-editor.org/rfc/rfc7950) definido para Prometheus (el modelo YANG se puede ver [aquí](docker/prometheus/yang-models/prometheus-pagoda.yang)). Este modelo YANG está influenciado por el [modelo de datos que propone Prometheus para modelar las métricas](https://github.com/OpenObservability/OpenMetrics/blob/main/specification/OpenMetrics.md) y por la especificación propuesta por la iniciativa [OpenMetrics](https://github.com/OpenObservability/OpenMetrics/blob/main/specification/OpenMetrics.md). Para poder automatizar el proceso de estructuración de los datos de las métricas de Prometheus originales de acuerdo al modelo YANG propuesto se ha desarrollado un procesador en NiFi programado como una aplicación Java que que se encarga de implementar dicha funcionalidad, haciendo uso de la librería [YANG Tools](https://docs.opendaylight.org/en/stable-sulfur/developer-guides/yang-tools.html) de OpenDayLight. Los datos de telemetría resultantes son enviados continuamente como datos de streaming a un bus de mensajes basado en una solución de [Apache Kafka](https://kafka.apache.org/) ([aquí](utils/prometheus-kafka-samples/yang-sample-iso8601/atica-node_network_transmit_packets_total-62f283db94774a15a79bb5aa.json) se representa una muestra ejemplo de una métrica resultante publicada en un _topic_ de un _broker_ de Kafka). La función del _Kafka Broker_ es actuar como un substrato de datos de telemetría al que los consumidores interesados pueden suscribirse. Apache Kafka es dependiente de un servicio denominado [Apache Zookeeper](https://zookeeper.apache.org/), pensado para la coordinación eficiente y escalable de sistemas distribuidos, que permite coordinar el intercambio de los datos entre _brokers_ distribuidos. Precisamente esta es la función del componente _Brokers Coordinator_ para poder coordinar el intercambio de datos de telemetría entre los _Kafka Brokers_ existentes en cada sede. Finalmente, cada sede tiene instalada y configurada una plataforma de monitorización (es decir, `Monitoring Platform` en la figura) basada en el _stack_ de Prometheus desde donde se obtiene la información de telemetría relativa a métricas de rendimiento de los servicios virtualizados desplegados en cada sede y a métricas de rendimiento general de la infraestructura de la propia sede. 

Para conocer con detalle la utilidad de las diferentes operaciones proporcionadas por la API del servicio `Telemetry Orchestrator` para la gestión de la telemetría basada en Prometheus, consulta la información [aquí](docs/prometheus-telemetry-openapi-recipe/README.md).

Una de las funcionalidades adicionales del servicio `Telemetry Orchestrator` es la opción de permitir activar el seguimiento activo de la localización de los equipos de usuarios o UEs (_User Equipments_) de los clientes móviles dentro de la infraestructura de red 5G de `PAGODA` mediante el uso subordinado de la API basada en REST y con especificación OpenAPI que proporciona la solución `NDAC Manager` de Nokia. Para conocer con detalle la utilidad de las diferentes operaciones proporcionadas por la API del servicio `Telemetry Orchestrator` para la localización de usuarios, consulta la información [aquí](docs/ue-location-openapi-recipe/README.md).

## Despliegue del prototipo del sistema de orquestación de telemetría

En este repositorio se encuentra un prototipo funcional del sistema de orquestación de telemetría basado en Docker.

Para desplegar el prototipo del sistema de orquestación de telemetría, execute el siguiente comando:
```bash
docker-compose -f docker-compose-full.yml up
```

En caso de que esté interesado en ejecutar el prototipo en segundo plano (los registros o _logs_ de los diferentes microservicios pueden ser molestos), use el siguiente comando:
```bash
docker-compose -f docker-compose-full.yml up -d
```

Para detener el sistema, ejecute lo siguiente:
```bash
docker-compose -f docker-compose-full.yml down
```

## Requisitos

- Docker (_probado con versión 19.03.13_)
- Docker-compose (_probado con la versión 1.27.4_)
- Python 3.9
- [Poetry](https://python-poetry.org/docs/)

# Agradecimientos
...