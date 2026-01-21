#pragma once

#include <stdexcept>
#include <DotNet/System/Exception.h>



namespace DotNet::Reinterop {

class ReinteropNativeException : public std::runtime_error {
public:
  ReinteropNativeException(const DotNet::System::Exception& exception);
  const ::DotNet::System::Exception& GetDotNetException() const;

private:
  ::DotNet::System::Exception _exception;
};

} // namespace DotNet::Reinterop


