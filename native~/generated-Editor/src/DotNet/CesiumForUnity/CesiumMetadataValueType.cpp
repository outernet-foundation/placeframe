#include <DotNet/CesiumForUnity/CesiumMetadataValueType.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumMetadataType.h>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>

namespace DotNet::CesiumForUnity {
struct CesiumMetadataValueType;
}

namespace DotNet::CesiumForUnity {

void (*CesiumMetadataValueType::Construct_RFYaAjfQVfO4__8eI7fs9pw)(::std::uint32_t type, ::std::uint32_t componentType, ::std::uint8_t isArray, ::DotNet::CesiumForUnity::CesiumMetadataValueType* pReturnValue, void** reinteropException) = nullptr;


CesiumMetadataValueType CesiumMetadataValueType::Construct(::DotNet::CesiumForUnity::CesiumMetadataType type, ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType, bool isArray)
{
    void* reinteropException = nullptr;
    CesiumMetadataValueType result;
    Construct_RFYaAjfQVfO4__8eI7fs9pw(::std::uint32_t(type), ::std::uint32_t(componentType), isArray ? 1 : 0, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumMetadataValueType::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::CesiumForUnity::CesiumMetadataValueType* pReturnValue, void** reinteropException) = nullptr;


CesiumMetadataValueType CesiumMetadataValueType::Construct()
{
    void* reinteropException = nullptr;
    CesiumMetadataValueType result;
    Construct_1B2M2Y8AsgTpgAmY7PhCfg(&result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


