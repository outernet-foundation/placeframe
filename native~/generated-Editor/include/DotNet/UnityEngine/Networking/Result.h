#pragma once





namespace DotNet::UnityEngine::Networking {

enum class Result {
  InProgress = 0,
  Success = 1,
  ConnectionError = 2,
  ProtocolError = 3,
  DataProcessingError = 4,
};

} // namespace DotNet::UnityEngine::Networking


