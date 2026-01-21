#include <DotNet/CesiumForUnity/CesiumIntMat3x3.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumIntVec3.h>
#include <cstdint>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec3;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntMat3x3;
}

namespace DotNet::CesiumForUnity {

void (*CesiumIntMat3x3::Construct_tv5P8Gb7SQuNjwU2Vh0zRw)(const ::DotNet::CesiumForUnity::CesiumIntVec3* v0, const ::DotNet::CesiumForUnity::CesiumIntVec3* v1, const ::DotNet::CesiumForUnity::CesiumIntVec3* v2, ::DotNet::CesiumForUnity::CesiumIntMat3x3* pReturnValue, void** reinteropException) = nullptr;


CesiumIntMat3x3 CesiumIntMat3x3::Construct(const ::DotNet::CesiumForUnity::CesiumIntVec3& v0, const ::DotNet::CesiumForUnity::CesiumIntVec3& v1, const ::DotNet::CesiumForUnity::CesiumIntVec3& v2)
{
    void* reinteropException = nullptr;
    CesiumIntMat3x3 result;
    Construct_tv5P8Gb7SQuNjwU2Vh0zRw(&v0, &v1, &v2, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumIntMat3x3::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumIntMat3x3* thiz, ::std::int32_t index, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIntVec3 CesiumIntMat3x3::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumIntVec3 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


